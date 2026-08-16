"""Read-only local-bounds audit for the five-stage Train A v735 press contract."""

import json
from pathlib import Path

import unreal


ROOT = "/Game/LineBoss/Developer/Validation/PressTrains/NewRigidIntake_v741/"
ROOT += "Cairnwell_S03_Movable_v632Controls_v735/StaticMeshes"
NAMES = (
    "S03_STATIC_SHELL",
    "S03_RAM_SLIDE",
    "S03_UPPER_DIE",
    "S03_LOWER_DIE_BOLSTER",
    "SM_CA_Factory_Elect_net_MeshyMaster_v632",
    "SM_CA_Factory_Opera_HMI_MeshyMaster_v632",
)
SCALE = 6.57
PANEL_DATUM_Z_CM = 202.221


rows = []
for name in NAMES:
    path = f"{ROOT}/{name}"
    mesh = unreal.EditorAssetLibrary.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"missing static mesh: {path}")
    box = mesh.get_bounding_box()
    rows.append(
        {
            "name": name,
            "path": mesh.get_path_name(),
            "bounds_min_cm": [box.min.x, box.min.y, box.min.z],
            "bounds_max_cm": [box.max.x, box.max.y, box.max.z],
            "scaled_min_z_cm": box.min.z * SCALE,
            "scaled_max_z_cm": box.max.z * SCALE,
        }
    )

by_name = {row["name"]: row for row in rows}
payload = {
    "status": "PASS__READ_ONLY_V735_PRESS_LOCAL_BOUNDS_AUDIT_V001",
    "scale": SCALE,
    "panel_datum_z_cm": PANEL_DATUM_Z_CM,
    "shell_floor_z_at_zero_component_z_cm": by_name["S03_STATIC_SHELL"]["scaled_min_z_cm"],
    "upper_die_underside_z_at_zero_component_z_cm": by_name["S03_UPPER_DIE"]["scaled_min_z_cm"],
    "required_shell_component_z_for_floor_seat_cm": -by_name["S03_STATIC_SHELL"]["scaled_min_z_cm"],
    "required_upper_die_component_z_for_panel_contact_cm": PANEL_DATUM_Z_CM
    - by_name["S03_UPPER_DIE"]["scaled_min_z_cm"],
    "meshes": rows,
}
out = Path(unreal.Paths.project_saved_dir()) / "Audits/PressTrains/press_train_a_v735_geometry_contract_v001.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log("LB_PRESS_TRAIN_A_V735_GEOMETRY_CONTRACT_V001=" + json.dumps(payload, sort_keys=True))
unreal.SystemLibrary.quit_editor()
