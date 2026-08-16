"""Create only the exact missing Coil AGV material dependencies referenced by retained meshes."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


DEST = "/Game/LineBoss/IndustrialKit/MaterialHandling/CoilAGV/Candidate_v001"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/coil_agv_missing_materials_repair_v001.json"
library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary

# name: (linear base colour, roughness, metallic, optional emissive colour)
SPECS = {
    "LB_AGV_BeaconAmber_v001": ((1.00, 0.34, 0.015), 0.24, 0.05, (2.8, 0.55, 0.015)),
    "LB_AGV_BlueDirectionLight_v001": ((0.015, 0.16, 0.75), 0.20, 0.02, (0.02, 0.34, 3.2)),
    "LB_AGV_CairnwellMark_v001": ((0.78, 0.86, 0.80), 0.48, 0.02, None),
    "LB_AGV_DeckSteel_v001": ((0.16, 0.19, 0.21), 0.32, 0.86, None),
    "LB_AGV_EStopRed_v001": ((0.72, 0.025, 0.015), 0.28, 0.02, None),
    "LB_AGV_FabricatedCharcoal_v001": ((0.025, 0.032, 0.038), 0.36, 0.72, None),
    "LB_AGV_HighLoadRubber_v001": ((0.008, 0.010, 0.012), 0.78, 0.00, None),
    "LB_AGV_SafetyYellow_v001": ((0.96, 0.47, 0.015), 0.34, 0.18, None),
    "LB_AGV_SensorGlass_v001": ((0.018, 0.06, 0.075), 0.12, 0.25, (0.015, 0.08, 0.10)),
    "LB_AGV_StatusGreen_v001": ((0.015, 0.55, 0.13), 0.20, 0.02, (0.02, 2.2, 0.20)),
    "LB_AGV_WheelPolyurethane_v001": ((0.055, 0.065, 0.072), 0.66, 0.00, None),
}

existing = [name for name in SPECS if library.does_asset_exist(f"{DEST}/{name}")]
if existing:
    raise RuntimeError(f"refusing to overwrite existing dependencies: {existing}")

created = []
for name, (colour, roughness, metallic, emission) in SPECS.items():
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
    if emission:
        emit = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -420, 370)
        emit.set_editor_property("constant", unreal.LinearColor(*emission, 1.0))
        mel.connect_material_property(emit, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(material)
    library.save_loaded_asset(material, only_if_is_dirty=False)
    created.append(f"{DEST}/{name}")

chassis = unreal.load_asset(f"{DEST}/SM_LB_CoilAGV_Chassis_Candidate_v001")
deck = unreal.load_asset(f"{DEST}/SM_LB_CoilAGV_LiftDeck_Candidate_v001")
failures = []
if not isinstance(chassis, unreal.StaticMesh):
    failures.append("retained Coil AGV chassis still fails to load")
if not isinstance(deck, unreal.StaticMesh):
    failures.append("retained Coil AGV lift deck still fails to load")

payload = {
    "$schema": "cairnwell/audit/coil-agv-missing-materials-repair-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__EXACT_MISSING_DEPENDENCIES_CREATED__RETAINED_MESHES_LOAD" if not failures else "FAIL",
    "destination": DEST,
    "created_assets": created,
    "overwritten_assets": [],
    "retained_meshes": [str(chassis.get_path_name()) if chassis else None, str(deck.get_path_name()) if deck else None],
    "engineering_or_authority_changes": 0,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
if failures:
    raise RuntimeError("; ".join(failures))
unreal.log(f"LB_COIL_AGV_MATERIAL_REPAIR::{json.dumps(payload)}")
unreal.SystemLibrary.quit_editor()
