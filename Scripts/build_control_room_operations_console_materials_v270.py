"""Create calibrated, original PBR materials for the operations HMI and keys."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


DEST = "/Game/LineBoss/Candidates/ControlRoom/OperationsConsole_v270/Materials"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/ControlRoom/control_room_operations_console_materials_v270.json"
library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
specs = {
    "M_CA_OperationsScreenDark_v270": ((0.004, 0.010, 0.008), 0.22, 0.18),
    "M_CA_OperationsButtonCharcoal_v270": ((0.012, 0.016, 0.017), 0.62, 0.02),
}
existing = [name for name in specs if library.does_asset_exist(f"{DEST}/{name}")]
if existing:
    raise RuntimeError(f"refusing to overwrite retained materials: {existing}")
created = []
for name, (colour, roughness, metallic) in specs.items():
    material = tools.create_asset(name, DEST, unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(f"could not create {name}")
    base = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -420, 0)
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -420, 140)
    rough.set_editor_property("r", roughness)
    metal = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -420, 250)
    metal.set_editor_property("r", metallic)
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.recompile_material(material)
    library.save_loaded_asset(material, only_if_is_dirty=False)
    created.append(f"{DEST}/{name}")
payload = {
    "$schema": "cairnwell/audit/control-room-operations-console-materials-v270/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__TWO_ORIGINAL_CALIBRATED_PBR_MATERIALS_CREATED__NOT_PROMOTED",
    "created_assets": created,
    "overwritten_assets": [],
    "map_changes": 0,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LINE_BOSS_OPERATIONS_CONSOLE_MATERIALS_V270::{json.dumps(payload)}")
unreal.SystemLibrary.quit_editor()
