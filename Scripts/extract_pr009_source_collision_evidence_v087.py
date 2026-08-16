"""Blender-side, read-only extraction of PR-009 source object and UCX evidence."""
import json
from datetime import datetime, timezone
from pathlib import Path
import bpy

root = Path(bpy.path.abspath("//")).parents[4]
out = root / "Saved/Audits/PR009_InMap_v087/source_collision_evidence.json"
static_assets = {
    "SM_CA_MW_PR009_BaseFrame_01", "SM_CA_MW_PR009_Carrier_01",
    "SM_CA_MW_PR009_ElectricalCabinet_01", "SM_CA_MW_PR009_GuardSet_01",
    "SM_CA_MW_PR009_HMI_01", "SM_CA_MW_PR009_InspectionHardware_01",
    "SM_CA_MW_PR009_InteractionHardware_01", "SM_CA_MW_PR009_ServiceSystems_01",
    "SM_CA_MW_PR009_TracePortal_01", "SM_CA_MW_PR009_VisionCentre_01",
}

def vector(v):
    return [round(float(value), 6) for value in v]

def row(obj):
    corners = [obj.matrix_world @ __import__("mathutils").Vector(corner) for corner in obj.bound_box]
    minimum = [min(point[index] for point in corners) for index in range(3)]
    maximum = [max(point[index] for point in corners) for index in range(3)]
    return {
        "name": obj.name,
        "mesh_datablock": obj.data.name,
        "export_asset": obj.get("export_asset"),
        "semantic": obj.get("semantic"),
        "location_m": vector(obj.matrix_world.translation),
        "rotation_euler_degrees": vector([value * 57.29577951308232 for value in obj.matrix_world.to_euler()]),
        "dimensions_m": vector(obj.dimensions),
        "bounds_min_m": vector(minimum),
        "bounds_max_m": vector(maximum),
        "vertices": len(obj.data.vertices),
        "triangles": sum(len(poly.vertices) - 2 for poly in obj.data.polygons),
    }

manifest_path = root / "SourceAssets/PR009/AutomatedBlankStacker/Candidate_v002/PR009_Audits/v002/PR009_FBX_EXPORT_MANIFEST_v002.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest_files = {Path(entry["file"]).stem: entry for entry in manifest["files"]}
groups = {}
missing_source_objects = []
for asset in sorted(static_assets):
    names = manifest_files[asset]["objects"]
    objects = []
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj is None or obj.type != "MESH":
            missing_source_objects.append({"asset": asset, "object": name})
        else:
            objects.append(obj)
    groups[asset] = [row(obj) for obj in sorted(objects, key=lambda item: item.name)]
ucx = [row(obj) for obj in sorted(bpy.data.objects, key=lambda item: item.name)
       if obj.type == "MESH" and obj.name.startswith("UCX_PR009_")]

payload = {
    "$schema": "cairnwell/audit/pr009-source-collision-evidence-v087/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "source_blend": bpy.data.filepath,
    "source_unit_scale": bpy.context.scene.unit_settings.scale_length,
    "source_length_unit": bpy.context.scene.unit_settings.length_unit,
    "static_groups": groups,
    "static_group_count": len(groups),
    "source_object_count": sum(len(value) for value in groups.values()),
    "missing_source_objects": missing_source_objects,
    "supplied_ucx_candidates": ucx,
    "supplied_ucx_count": len(ucx),
    "assessment": {
        "binding_valid_as_supplied": False,
        "reason": "Names do not match any of the ten combined render meshes; large Infeed/Lift/Output/Gantry envelopes would close required process or material paths.",
        "reuse_policy": "Use accurate cabinet, HMI and segmented guard dimensions as source evidence; author deterministic per-render-asset primitives for release.",
    },
    "promotion_authorized": False,
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(f"PR009_V087_SOURCE_COLLISION_EVIDENCE output={out}")
