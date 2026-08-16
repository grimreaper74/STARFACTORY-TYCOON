"""Independent clean-scene FBX gate for PR-004 film dewrapper v006."""

from collections import Counter
from datetime import datetime
import json
import math
from pathlib import Path
import bpy

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "SourceAssets/PR004/FilmDewrapSpindle_v006"
MANIFEST = ROOT / "pr004_film_dewrap_spindle_candidate_v006_manifest.json"
AUDIT = REPO / "Saved/Audits/pr004_film_dewrap_spindle_candidate_v006_independent.json"
BOUND_TOLERANCE_MM = 1.0
PIVOT_TOLERANCE_MM = 0.25
ROTATION_TOLERANCE_DEG = 0.05


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.curves, bpy.data.armatures,
                       bpy.data.cameras, bpy.data.lights, bpy.data.materials):
        for block in list(collection):
            if block.users == 0:
                collection.remove(block)


def scalar_props(obj):
    return {key: obj[key] for key in obj.keys()
            if key != "_RNA_UI" and isinstance(obj[key], (str, int, float, bool))}


def material_record(material):
    alpha = [float(material.diffuse_color[3])]
    transparent = []
    linked_alpha = []
    if material.use_nodes and material.node_tree:
        for node in material.node_tree.nodes:
            if node.bl_idname in {"ShaderNodeBsdfTransparent", "ShaderNodeHoldout"}:
                transparent.append(node.name)
            if node.bl_idname == "ShaderNodeBsdfPrincipled":
                socket = node.inputs.get("Alpha")
                if socket:
                    alpha.append(float(socket.default_value))
                    if socket.is_linked:
                        linked_alpha.append(node.name)
    return {"name": material.name, "minimum_alpha": min(alpha),
            "transparent_nodes": transparent, "linked_alpha": linked_alpha,
            "opaque": min(alpha) >= 0.999 and not transparent and not linked_alpha}


def audit_module(module):
    path = Path(module["fbx"])
    clear_scene()
    bpy.ops.import_scene.fbx(filepath=str(path), use_custom_props=True)
    objects = list(bpy.context.scene.objects)
    meshes = [obj for obj in objects if obj.type == "MESH"]
    if len(meshes) != 1:
        return {"id": module["id"], "fbx": str(path),
                "object_types": dict(Counter(obj.type for obj in objects)),
                "checks": {"exactly_one_mesh": False}, "pass": False}
    obj = meshes[0]
    bounds_mm = [float(value) * 1000.0 for value in obj.dimensions]
    expected_mm = [float(value) * 10.0 for value in module["bounds_cm"]]
    bounds_delta = [abs(a-b) for a,b in zip(bounds_mm, expected_mm)]
    pivot_mm = [abs(float(value))*1000.0 for value in obj.location]
    rotation = [abs(math.degrees(float(value))) for value in obj.rotation_euler]
    scale_delta = [abs(float(value)-1.0) for value in obj.scale]
    triangles = sum(max(0, len(poly.vertices)-2) for poly in obj.data.polygons)
    expected_props = module.get("properties", {})
    actual_props = scalar_props(obj)
    missing_props = sorted(key for key in expected_props if key not in actual_props)
    mismatched_props = {key:{"expected":value,"actual":actual_props.get(key)}
                        for key,value in expected_props.items()
                        if key in actual_props and actual_props[key] != value}
    materials = [material_record(slot.material) for slot in obj.material_slots if slot.material]
    checks = {
        "exactly_one_mesh": True,
        "name_matches": obj.name == module["object"],
        "bounds_match": max(bounds_delta, default=0) <= BOUND_TOLERANCE_MM,
        "pivot_at_export_origin": max(pivot_mm, default=0) <= PIVOT_TOLERANCE_MM,
        "rotation_identity": max(rotation, default=0) <= ROTATION_TOLERANCE_DEG,
        "unit_scale": max(scale_delta, default=0) <= 0.0001,
        "positive_finite_bounds": all(value > 0 and math.isfinite(value) for value in bounds_mm),
        "finite_vertices": all(math.isfinite(axis) for vertex in obj.data.vertices for axis in vertex.co),
        "triangles_match": triangles == int(module["triangles"]),
        "metadata_matches": not missing_props and not mismatched_props,
        "materials_present_and_opaque": bool(materials) and all(item["opaque"] for item in materials),
        "no_extra_objects": len(objects) == 1,
    }
    return {"id":module["id"], "fbx":str(path), "imported_name":obj.name,
            "actual":{"bounds_mm":[round(v,3) for v in bounds_mm],
                      "pivot_mm":[round(v,4) for v in pivot_mm],
                      "rotation_deg":[round(v,5) for v in rotation],
                      "triangles":triangles, "materials":materials},
            "deltas":{"bounds_mm":[round(v,4) for v in bounds_delta]},
            "metadata":{"missing":missing_props,"mismatched":mismatched_props},
            "checks":checks, "pass":all(checks.values())}


manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
modules = manifest.get("modules", [])
if len(modules) != 14:
    raise RuntimeError(f"Expected 14 modules, got {len(modules)}")
results = [audit_module(module) for module in modules]
paths = [Path(module["fbx"]) for module in modules]
global_checks = {
    "candidate_not_promoted": manifest.get("status") == "SOURCE_CANDIDATE_NOT_PROMOTED",
    "fourteen_modules": len(modules) == 14,
    "unique_ids": len({module["id"] for module in modules}) == 14,
    "unique_names": len({module["object"] for module in modules}) == 14,
    "all_fbx_exist": all(path.is_file() and path.stat().st_size > 0 for path in paths),
    "folder_fbx_count_matches": len(list(ROOT.glob("*.fbx"))) == 14,
    "all_versioned_v006": all(path.stem.endswith("_v006") for path in paths),
    "all_clean_reimports_pass": all(result["pass"] for result in results),
    "no_uasset_in_source_folder": not any(ROOT.rglob("*.uasset")),
}
technical_pass = all(global_checks.values())
status = "SOURCE_FBX_GATE_PASS__CANDIDATE_NOT_PROMOTED" if technical_pass else "SOURCE_FBX_GATE_FAIL__CANDIDATE_NOT_PROMOTED"
audit = {"$schema":"line-boss/audit/pr004-film-dewrap-spindle-v006-independent/v1",
         "status":status, "independent_review":True,
         "timestamp":datetime.now().astimezone().isoformat(),
         "method":"Blender 5.2 clean-scene import of each exported FBX",
         "manifest":str(MANIFEST), "module_count":len(modules),
         "tolerances":{"bounds_mm":BOUND_TOLERANCE_MM,"pivot_mm":PIVOT_TOLERANCE_MM,"rotation_deg":ROTATION_TOLERANCE_DEG},
         "global_checks":global_checks, "technical_source_pass":technical_pass,
         "module_results":results,
         "scope_limit":"No Unreal import, collision, animation, interlock, persistence or promotion performed.",
         "promotion":"FORBIDDEN. Technical source gate alone is insufficient."}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(audit, indent=2)+"\n", encoding="utf-8")
print(json.dumps({"status":status,"modules":len(modules),"pass":technical_pass,"audit":str(AUDIT)}, indent=2))
