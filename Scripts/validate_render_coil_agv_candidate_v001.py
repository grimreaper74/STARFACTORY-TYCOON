"""Independently inspect the two exported coil-AGV FBX modules."""

from pathlib import Path
import hashlib
import json

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "SourceAssets/IndustrialKit/MaterialHandling/CoilAGV/Candidate_v001"
OUT = ROOT / "Saved/Audits/coil_agv_candidate_v001_fbx_validation.json"


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inspect(path):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.fbx(filepath=str(path), use_custom_normals=True)
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    corners = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    low = Vector((min(v.x for v in corners), min(v.y for v in corners), min(v.z for v in corners)))
    high = Vector((max(v.x for v in corners), max(v.y for v in corners), max(v.z for v in corners)))
    return {
        "fbx": str(path), "sha256": sha256(path), "mesh_count": len(meshes),
        "bounds_mm": [round((high[i]-low[i])*1000.0, 2) for i in range(3)],
        "min_mm": [round(low[i]*1000.0, 2) for i in range(3)],
        "max_mm": [round(high[i]*1000.0, 2) for i in range(3)],
        "vertices": sum(len(obj.data.vertices) for obj in meshes),
        "triangles": sum(sum(max(0, len(poly.vertices)-2) for poly in obj.data.polygons) for obj in meshes),
        "materials": sorted({slot.material.name for obj in meshes for slot in obj.material_slots if slot.material}),
        "custom_properties": {key: meshes[0][key] for key in meshes[0].keys() if key not in {"cycles"}} if len(meshes)==1 else {},
    }


results = {
    "$schema": "cairnwell/audit/coil-agv-candidate-v001-fbx-validation/v1",
    "status": "PASS" ,
    "modules": {
        "chassis": inspect(SOURCE / "SM_LB_CoilAGV_Chassis_Candidate_v001.fbx"),
        "lift_deck": inspect(SOURCE / "SM_LB_CoilAGV_LiftDeck_Candidate_v001.fbx"),
    },
    "requirements": {
        "chassis_max_xy_mm": [3620, 2230], "payload_design_target_kg": 40000,
        "payload_certification": "TBC", "promotion_authorized": False,
    },
}
chassis = results["modules"]["chassis"]
if chassis["bounds_mm"][0] > 3620 or chassis["bounds_mm"][1] > 2230:
    results["status"] = "FAIL_CHASSIS_ENVELOPE"
OUT.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
print(json.dumps(results, indent=2, default=str))
if results["status"] != "PASS":
    raise RuntimeError(results["status"])
