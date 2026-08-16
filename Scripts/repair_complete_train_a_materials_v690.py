"""Create and bind exact zero-credit fallback materials for Train A missing slots."""
from pathlib import Path
from datetime import datetime, timezone
import json
import unreal

ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / r"Saved\Audits\PressTrains\complete_train_a_material_slots_v689.json"
OUT = ROOT / r"Saved\Audits\PressTrains\complete_train_a_material_repair_v690.json"
DEST = "/Game/LineBoss/Developer/Validation/PressTrains/TrainAMaterials_v690"
library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
if OUT.exists():
    raise RuntimeError("Refusing to overwrite v690")

# name: (linear base colour, roughness, metallic, optional emissive)
SPECS = {
    "M_LB_PTA_CairnwellGreen_v690": ((0.025, 0.19, 0.085), 0.36, 0.62, None),
    "M_LB_PTA_SafetyYellow_v690": ((0.95, 0.47, 0.012), 0.34, 0.20, None),
    "M_LB_PTA_FabricatedGraphite_v690": ((0.028, 0.036, 0.043), 0.42, 0.70, None),
    "M_LB_PTA_MachinedSteel_v690": ((0.34, 0.39, 0.43), 0.25, 0.92, None),
    "M_LB_PTA_ElectricalGrey_v690": ((0.30, 0.33, 0.35), 0.52, 0.28, None),
    "M_LB_PTA_TrimRed_v690": ((0.52, 0.018, 0.012), 0.44, 0.15, None),
    "M_LB_PTA_ProcessBlue_v690": ((0.025, 0.14, 0.42), 0.38, 0.34, None),
    "M_LB_PTA_RubberBlack_v690": ((0.007, 0.009, 0.012), 0.80, 0.00, None),
    "M_LB_PTA_HMIScreen_v690": ((0.008, 0.055, 0.075), 0.16, 0.10, (0.01, 0.42, 0.62)),
}
existing = [name for name in SPECS if library.does_asset_exist(f"{DEST}/{name}")]
if existing:
    raise RuntimeError(f"Refusing to overwrite material assets: {existing}")

materials = {}
created = []
for name, (colour, roughness, metallic, emission) in SPECS.items():
    material = tools.create_asset(name, DEST, unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(f"Could not create {name}")
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
    materials[name] = material
    created.append(material.get_path_name())

def choose(asset_path):
    if any(token in asset_path for token in ("Fence", "Gate", "LeftDoor", "RightDoor", "DieCart", "Stillage")):
        return "M_LB_PTA_SafetyYellow_v690"
    if "HMI" in asset_path:
        return "M_LB_PTA_HMIScreen_v690"
    if any(token in asset_path for token in ("UpperDie", "LowerDie", "RamSlide", "Rotor", "Transfer", "PoweredConveyor")):
        return "M_LB_PTA_MachinedSteel_v690"
    if any(token in asset_path for token in ("TrimScrap", "SlugCollection")):
        return "M_LB_PTA_TrimRed_v690"
    if any(token in asset_path for token in ("LargeTrimBin", "SmallSlugBin")):
        return "M_LB_PTA_ProcessBlue_v690"
    if any(token in asset_path for token in ("Cabinet", "Housing")):
        return "M_LB_PTA_ElectricalGrey_v690"
    if any(token in asset_path for token in ("StaticPressShell", "HPU", "Destack", "InspectUnload")):
        return "M_LB_PTA_CairnwellGreen_v690"
    return "M_LB_PTA_FabricatedGraphite_v690"

inventory = json.loads(SOURCE.read_text(encoding="utf-8"))
bindings = []
failures = []
for row in inventory["assets"]:
    mesh = unreal.load_asset(row["asset"])
    if not isinstance(mesh, unreal.StaticMesh):
        failures.append(f"mesh failed to load: {row['asset']}")
        continue
    chosen = choose(row["asset"])
    for slot in row["slots"]:
        # Repair missing dependencies and replace the two validation grid materials.
        if slot["current_material"] and slot["current_material"] != "/Engine/EngineMaterials/WorldGridMaterial.WorldGridMaterial":
            continue
        mesh.set_material(slot["index"], materials[chosen])
        bindings.append({
            "mesh": row["asset"],
            "slot": slot["index"],
            "imported_slot": slot["imported_material_slot_name"],
            "material": materials[chosen].get_path_name(),
        })
    if any(binding["mesh"] == row["asset"] for binding in bindings):
        library.save_loaded_asset(mesh, only_if_is_dirty=False)

for binding in bindings:
    mesh = unreal.load_asset(binding["mesh"])
    actual = mesh.get_material(binding["slot"]) if mesh else None
    if not actual or actual.get_path_name() != binding["material"]:
        failures.append(f"binding verification failed: {binding['mesh']} slot {binding['slot']}")

status = "PASS__EXACT_MISSING_AND_GRID_MATERIAL_BINDINGS_REPAIRED" if not failures else "FAIL"
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "revision": "v690",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": status,
    "created_material_assets": created,
    "binding_count": len(bindings),
    "bindings": bindings,
    "failures": failures,
    "geometry_changes": 0,
    "collision_changes": 0,
    "authority_changes": 0,
    "meshy_credits_used": 0,
    "protected_map_modified": False,
}, indent=2), encoding="utf-8")
if failures:
    raise RuntimeError("; ".join(failures))
unreal.log("LINE_BOSS_COMPLETE_TRAIN_A_MATERIAL_REPAIR_V690_PASS")
