"""Read-only Blender audit for Claude's MaterialFlow RuntimePrep v001 FBXs.

Run with Blender 5.2 headless.  It verifies that the published RuntimePrep
triangle fields describe the actual exported FBX payload before Unreal imports
the pack.  Results are written only under Saved/Audits.
"""

import hashlib
import json
import re
import sys
import traceback
from pathlib import Path

import bpy
from mathutils import Vector


PROJECT_ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
RUNTIME_ROOT = PROJECT_ROOT / "ArtSource/Claude_PressShop_MaterialFlowPack_RuntimePrep_v001"
STATS = RUNTIME_ROOT / "runtime_prep_stats.json"
OUT = (PROJECT_ROOT / "Saved/Audits/OneFactory/Press/MaterialFlowPackRuntimePrep_v001/"
       "fbx_payload_audit_retry1.json")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)


def canonical_material_name(name):
    """Remove Blender's local duplicate suffix without changing slot order.

    Each FBX carries its own copy of shared CA_MW materials.  Importing the six
    files into one temporary Blender process makes Blender append ``.001`` etc.
    That is an importer-local alias, not a changed source semantic.
    """
    return re.sub(r"\.\d{3}$", "", name) if name else None


def world_bounds(obj):
    vertices = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    if not vertices:
        return None
    low = Vector((min(v.x for v in vertices), min(v.y for v in vertices), min(v.z for v in vertices)))
    high = Vector((max(v.x for v in vertices), max(v.y for v in vertices), max(v.z for v in vertices)))
    return {
        "min": [round(value, 6) for value in low],
        "max": [round(value, 6) for value in high],
    }


def audit_module(module_name, module):
    fbx = RUNTIME_ROOT / module["file"]
    clear_scene()
    bpy.ops.import_scene.fbx(filepath=str(fbx), use_manual_orientation=False)
    mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    expected_meshes = module["meshes"]
    meshes = {}
    failures = []
    for obj in mesh_objects:
        obj.data.calc_loop_triangles()
        triangles = len(obj.data.loop_triangles)
        raw_slots = [slot.material.name if slot.material else None for slot in obj.material_slots]
        meshes[obj.name] = {
            "triangles": triangles,
            "material_slots_raw": raw_slots,
            "material_slots": [canonical_material_name(name) for name in raw_slots],
            "uv_layers": [layer.name for layer in obj.data.uv_layers],
            "object_location": [round(value, 6) for value in obj.location],
            "world_bounds": world_bounds(obj),
        }
    if set(meshes) != set(expected_meshes):
        failures.append("exported mesh names differ from RuntimePrep stats")
    for mesh_name, expected in expected_meshes.items():
        actual = meshes.get(mesh_name)
        if actual is None:
            continue
        if actual["triangles"] != int(expected["triangles"]):
            failures.append(
                f"{mesh_name}: FBX={actual['triangles']}, stats={expected['triangles']}")
        if actual["uv_layers"] != expected["uv_layers"]:
            failures.append(f"{mesh_name}: UV layer names drifted")
        if actual["material_slots"] != expected["material_slots"]:
            failures.append(f"{mesh_name}: semantic material slot order drifted")
    actual_hash = sha256(fbx)
    if actual_hash != module["fbx_sha256"]:
        failures.append("FBX sha256 differs from RuntimePrep provenance")
    return {
        "file": str(fbx),
        "sha256": actual_hash,
        "published_sha256": module["fbx_sha256"],
        "meshes": meshes,
        "failures": failures,
    }


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        stats = json.loads(STATS.read_text(encoding="utf-8"))
        modules = {}
        failures = []
        for module_name, module in stats["modules"].items():
            result = audit_module(module_name, module)
            modules[module_name] = result
            failures.extend(f"{module_name}: {failure}" for failure in result["failures"])
        result = {
            "$schema": "lineboss/audit/onefactory/press/material-flow-fbx-payload/v1",
            "source_runtimeprep_stats": str(STATS),
            "source_runtimeprep_stats_sha256": sha256(STATS),
            "modules": modules,
            "published_exported_triangles_total": stats["reconstruction"]["exported_triangles_total"],
            "audited_exported_triangles_total": sum(
                mesh["triangles"]
                for module in modules.values()
                for mesh in module["meshes"].values()),
            "failures": failures,
            "status": "PASS__MATERIAL_FLOW_FBX_PAYLOAD_MATCHES_RUNTIMEPREP"
            if not failures else "FAIL__MATERIAL_FLOW_FBX_PAYLOAD_MISMATCH",
            "write_scope": [str(OUT)],
            "source_content_writes": [],
        }
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if failures:
            raise RuntimeError("; ".join(failures))
    except Exception:
        if not OUT.exists():
            OUT.write_text(json.dumps({
                "status": "FAIL__MATERIAL_FLOW_FBX_PAYLOAD_AUDIT_ERROR",
                "traceback": traceback.format_exc(),
                "write_scope": [str(OUT)],
                "source_content_writes": [],
            }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        raise


main()
