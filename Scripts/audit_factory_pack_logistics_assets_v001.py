"""Read-only technical audit of the contained licensed logistics shortlist."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = "/Game/LineBoss/Vendor/FactoryEnvironment/Logistics/Meshes"
NAMES = (
    "SM_ForkLift", "SM_Forklift_prop_grate", "SM_Forklift_prop_light",
    "SM_Forklift_prop_seat", "SM_Forklift_prop_wheel", "SM_PalletCart",
    "SM_PalletCart_box", "SM_PalletCart_PalletBox_open",
    "SM_PlasticPallet01", "SM_AssemblyLineCrate01")
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/factory_pack_logistics_asset_audit_v001.json"
library = unreal.EditorAssetLibrary
rows = []

for name in NAMES:
    path = f"{ROOT}/{name}"
    mesh = library.load_asset(path)
    if mesh is None or not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing contained static mesh {path}")
    bounds = mesh.get_bounds().box_extent * 2.0
    materials = [
        {
            "slot": str(slot.get_editor_property("material_slot_name")),
            "material": (slot.get_editor_property("material_interface").get_path_name()
                         if slot.get_editor_property("material_interface") else None),
        }
        for slot in mesh.get_editor_property("static_materials")
    ]
    rows.append({
        "asset": mesh.get_path_name(),
        "bounds_cm": [bounds.x, bounds.y, bounds.z],
        "material_slots": materials,
        "lod_count": mesh.get_num_lods(),
        "collision_complexity": str(mesh.get_editor_property("body_setup").get_editor_property("collision_trace_flag")),
    })

payload = {
    "$schema": "line-boss/audit/factory-pack-logistics-assets-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "CONTAINED_LICENSED_LOGISTICS_ASSETS_LOAD_PASS__VISUAL_GATE_REQUIRED__NOT_PROMOTED",
    "assets": rows,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_FACTORY_LOGISTICS_ASSET_AUDIT_PASS assets={len(rows)}")

