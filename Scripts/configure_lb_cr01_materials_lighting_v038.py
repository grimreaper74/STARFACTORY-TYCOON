"""Restore a readable industrial palette and calibrated validation lighting for CR01 v038."""
import json
from pathlib import Path
import unreal

DEST = "/Game/LineBoss/Shared/SupportRobots/LB_CR01/Candidate_v038_ModularRig"
MAP = "/Game/LineBoss/Developer/Validation/LB_CR01_CleaningAMR_ModularRig_v038"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/lb_cr01_material_lighting_v038.json"
asset_lib = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary

PALETTE = {
    "BodyCharcoal": ((0.055, 0.065, 0.070), 0.48, 0.72),
    "FrameAnthracite": ((0.025, 0.030, 0.034), 0.68, 0.68),
    "SafetyYellow": ((0.92, 0.53, 0.025), 0.15, 0.43),
    "RubberBlack": ((0.012, 0.014, 0.016), 0.02, 0.88),
    "RenewedRubber": ((0.018, 0.022, 0.024), 0.01, 0.78),
    "BrushedSteel": ((0.31, 0.34, 0.36), 0.78, 0.34),
    "ServicePlate_SS304": ((0.40, 0.43, 0.45), 0.82, 0.28),
    "ServicePlate_Engrave": ((0.015, 0.018, 0.020), 0.35, 0.62),
    "ServiceFastener": ((0.12, 0.14, 0.15), 0.82, 0.30),
    "RecessBlack": ((0.006, 0.008, 0.009), 0.05, 0.78),
    "Bristle": ((0.018, 0.020, 0.018), 0.00, 0.92),
    "SensorGlass": ((0.018, 0.075, 0.095), 0.38, 0.18),
    "LensVertexTint": ((0.045, 0.19, 0.24), 0.30, 0.20),
    "CertificationMark": ((0.10, 0.56, 0.22), 0.05, 0.55),
    "DormantDust": ((0.17, 0.135, 0.085), 0.00, 0.94),
    "DormantOxide": ((0.24, 0.065, 0.018), 0.08, 0.90),
    "Condition_Oxide": ((0.20, 0.052, 0.014), 0.10, 0.88),
    "MothballedGrime": ((0.075, 0.060, 0.040), 0.00, 0.96),
}

def spec_for(name):
    for token, spec in PALETTE.items():
        if token in name:
            return spec
    return ((0.12, 0.13, 0.14), 0.35, 0.62)

MAT_DEST = DEST + "/Materials"
tools = unreal.AssetToolsHelpers.get_asset_tools()
configured = []
replacement = {}
for token, (color, metallic, roughness) in PALETTE.items():
    asset_name = "M_LB_CR01_V038_" + token
    path = MAT_DEST + "/" + asset_name
    material = unreal.load_asset(path)
    if material is None:
        material = tools.create_asset(asset_name, MAT_DEST, unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(f"Could not create {path}")
    mel.delete_all_material_expressions(material)
    base = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -400, -50)
    base.set_editor_property("constant", unreal.LinearColor(*color, 1.0))
    metal = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -400, 50)
    metal.set_editor_property("r", metallic)
    rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -400, 150)
    rough.set_editor_property("r", roughness)
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    mel.recompile_material(material)
    asset_lib.save_loaded_asset(material, only_if_is_dirty=False)
    configured.append(material.get_name())
    replacement[token] = material

assigned_slots = 0
for path in asset_lib.list_assets(DEST, recursive=False, include_folder=False):
    mesh = unreal.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh):
        continue
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        interface = slot.get_editor_property("material_interface")
        source_name = interface.get_name() if interface else str(slot.get_editor_property("material_slot_name"))
        target = next((mat for token, mat in replacement.items() if token in source_name), replacement["FrameAnthracite"])
        mesh.set_material(index, target)
        assigned_slots += 1
    asset_lib.save_loaded_asset(mesh, only_if_is_dirty=False)

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    if label == "LB_CR01_V038_KeyLight":
        actor.get_editor_property("directional_light_component").set_editor_property("intensity", 0.65)
    elif label == "LB_CR01_V038_SkyLight":
        actor.get_editor_property("light_component").set_editor_property("intensity", 0.22)
    elif label.startswith("LB_CR01_V038_Fill"):
        actor.get_editor_property("point_light_component").set_editor_property("intensity", 65.0)
if not levels.save_current_level():
    raise RuntimeError("Could not save calibrated CR01 validation level")
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "status": "MATERIAL_AND_LIGHTING_CONFIGURATION_PASS__VISUAL_GATE_PENDING",
    "material_count": len(configured), "assigned_mesh_slots": assigned_slots, "materials": sorted(configured),
    "lighting": {"directional_lux": 0.65, "skylight": 0.22, "point_lights_lm": 65.0},
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_LB_CR01_V038_MATERIAL_LIGHTING_PASS")
