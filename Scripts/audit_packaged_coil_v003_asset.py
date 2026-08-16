"""Read-only audit of the existing dimensioned packaged-coil v003 import."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ASSET = "/Game/LineBoss/IndustrialKit/MaterialHandling/PR003Candidate_v011/SM_LB_MasterCoil_Candidate_v003"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/packaged_coil_v003_existing_asset.json"
mesh = unreal.load_asset(ASSET)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError(f"Missing {ASSET}")
box = mesh.get_bounding_box()
materials = []
for index, slot in enumerate(mesh.get_editor_property("static_materials")):
    material = slot.get_editor_property("material_interface")
    materials.append({
        "index": index,
        "slot": str(slot.get_editor_property("imported_material_slot_name")
                    or slot.get_editor_property("material_slot_name")),
        "material": material.get_path_name() if material else None,
    })
body = mesh.get_editor_property("body_setup")
payload = {
    "$schema": "line-boss/audit/packaged-coil-v003-existing-asset/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "asset": mesh.get_path_name(),
    "bounds_cm": [
        box.max.x - box.min.x,
        box.max.y - box.min.y,
        box.max.z - box.min.z,
    ],
    "lod_count": mesh.get_num_lods(),
    "material_slots": materials,
    "simple_collision_primitive_count": int(unreal.EditorStaticMeshLibrary.get_simple_collision_count(mesh)),
    "collision_trace_flag": str(body.get_editor_property("collision_trace_flag")),
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PACKAGED_COIL_V003_AUDIT_PASS output={OUT}")
unreal.SystemLibrary.quit_editor()
