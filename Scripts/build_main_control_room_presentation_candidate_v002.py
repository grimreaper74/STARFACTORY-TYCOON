"""Create isolated v002 control-room presentation with UE-native materials/cameras."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_MainControlRoom_IntegrationCandidate_v001"
MAP = "/Game/LineBoss/Maps/LB_MainControlRoom_PresentationCandidate_v002"
SRC = "/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v001/Meshes"
DEST = "/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v002"
MAT = DEST + "/Materials"
OUT = ROOT / "Saved/Audits/ControlRoom/main_control_room_presentation_build_v002.json"

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP}")

palette = {
    "M_CA_FoundryCharcoal_R": ((0.035, 0.045, 0.044), 0.05, 0.68, None),
    "M_CA_CairnwellGreen_R": ((0.012, 0.200, 0.115), 0.05, 0.54, None),
    "M_CA_StatusGreen_R": ((0.010, 0.080, 0.045), 0.02, 0.42, (0.04, 0.55, 0.25)),
    "M_CA_SafetyYellow_R": ((0.950, 0.520, 0.015), 0.05, 0.48, None),
    "M_CA_EquipmentLightGrey_R": ((0.160, 0.190, 0.190), 0.08, 0.58, None),
    "M_CA_BrushedSteel_R": ((0.280, 0.320, 0.330), 0.72, 0.32, None),
    "M_CA_Galvanised_R": ((0.420, 0.460, 0.450), 0.58, 0.46, None),
    "M_CA_RubberFloor_R": ((0.025, 0.030, 0.029), 0.0, 0.88, None),
    "M_CA_LaminatedGlass_R": ((0.035, 0.120, 0.130), 0.05, 0.18, None),
    "M_CA_ScreenDark_R": ((0.004, 0.018, 0.017), 0.0, 0.22, (0.008, 0.060, 0.050)),
    "M_CA_ScreenBlue_R": ((0.005, 0.025, 0.040), 0.0, 0.22, (0.015, 0.160, 0.250)),
    "M_CA_Alarm_R": ((0.160, 0.008, 0.004), 0.0, 0.30, (0.65, 0.025, 0.010)),
    "M_CA_DiagnosticCyan_R": ((0.005, 0.120, 0.160), 0.0, 0.26, (0.015, 0.45, 0.65)),
    "M_CA_MinorAmber_R": ((0.350, 0.200, 0.002), 0.0, 0.30, (0.75, 0.34, 0.01)),
    "M_CA_Light_R": ((0.420, 0.470, 0.440), 0.0, 0.34, (0.85, 0.95, 0.88)),
    "M_CA_TextEmission_R": ((0.480, 0.520, 0.500), 0.0, 0.34, (0.55, 0.75, 0.68)),
    "M_CA_EStopRed_R": ((0.550, 0.005, 0.002), 0.0, 0.36, None),
    "M_CA_ChairFabric_R": ((0.018, 0.022, 0.021), 0.0, 0.92, None),
    "M_CA_MothballedCover_M": ((0.070, 0.065, 0.055), 0.0, 0.94, None),
    "M_CA_MothballedDust_M": ((0.180, 0.155, 0.115), 0.0, 0.98, None),
    "M_CA_ScreenOff_M": ((0.003, 0.004, 0.004), 0.0, 0.46, None),
}


def make_material(name, base, metallic, roughness, emissive):
    material = asset_tools.create_asset(name + "_v002", MAT, unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(name)
    colour = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -320, -80)
    colour.set_editor_property("constant", unreal.LinearColor(*base, 1.0))
    metal = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -320, 50)
    metal.set_editor_property("r", metallic)
    rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -320, 130)
    rough.set_editor_property("r", roughness)
    mel.connect_material_property(colour, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    if emissive is not None:
        glow = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -320, 230)
        glow.set_editor_property("constant", unreal.LinearColor(*emissive, 1.0))
        mel.connect_material_property(glow, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(material)
    library.save_loaded_asset(material, only_if_is_dirty=False)
    return material


materials = {name: make_material(name, *values) for name, values in palette.items()}
categories = (
    "Architecture", "Consoles", "Systems", "Furniture", "Interaction",
    "Service", "Identity", "State_Restored", "State_Mothballed",
)
mesh_paths = {}
failures = []
for category in categories:
    source_path = f"{SRC}/SM_CA_MW_MCR_{category}_v001"
    target_path = f"{DEST}/Meshes/SM_CA_MW_MCR_{category}_v002"
    mesh = library.duplicate_asset(source_path, target_path)
    if not isinstance(mesh, unreal.StaticMesh):
        failures.append(f"mesh duplicate failed: {source_path}")
        continue
    static_materials = mesh.get_editor_property("static_materials")
    for index, slot in enumerate(static_materials):
        slot_name = str(slot.get_editor_property("material_slot_name"))
        replacement = materials.get(slot_name)
        if replacement is None:
            failures.append(f"no v002 material for {category} slot {slot_name}")
        else:
            mesh.set_material(index, replacement)
    library.save_loaded_asset(mesh, only_if_is_dirty=False)
    mesh_paths[category] = target_path

actors = {actor.get_actor_label(): actor for actor in actors_api.get_all_level_actors()}
for category, mesh_path in mesh_paths.items():
    actor = actors.get(f"LB_MCR_V001_{category}")
    mesh = library.load_asset(mesh_path)
    if actor is None or not isinstance(mesh, unreal.StaticMesh):
        failures.append(f"missing map actor or v002 mesh for {category}")
        continue
    actor.static_mesh_component.set_editor_property("static_mesh", mesh)
    actor.set_actor_label(f"LB_MCR_V002_{category}")
    actor.tags = [unreal.Name("LB.ControlRoom.v002"), unreal.Name(f"LB.ControlRoom.Category.{category}"), unreal.Name("LB.Asset.CandidateNotPromoted")]

for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    if label.startswith("LB_MCR_V001_CeilingLight_"):
        actor.set_actor_label(label.replace("V001", "V002"))
        component = actor.get_component_by_class(unreal.RectLightComponent)
        component.set_editor_property("intensity", 240.0)
        actor.tags = [unreal.Name("LB.ControlRoom.v002"), unreal.Name("LB.ControlRoom.Lighting.Restored"), unreal.Name("LB.Asset.CandidateNotPromoted")]

exposure = actors_api.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(), unreal.Rotator())
exposure.set_actor_label("LB_MCR_V002_Exposure")
exposure.set_editor_property("unbound", True)
settings = exposure.get_editor_property("settings")
settings.set_editor_properties({
    "override_auto_exposure_method": True,
    "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
    "override_auto_exposure_min_brightness": True,
    "override_auto_exposure_max_brightness": True,
    "auto_exposure_min_brightness": 1.0,
    "auto_exposure_max_brightness": 1.0,
    "override_auto_exposure_bias": True,
    "auto_exposure_bias": -1.65,
})
exposure.set_editor_property("settings", settings)
exposure.tags = [unreal.Name("LB.ControlRoom.v002"), unreal.Name("LB.Asset.CandidateNotPromoted")]

camera_specs = {
    "SeatedPlayer": (unreal.Vector(0, 38, 112), unreal.Vector(0, -330, 180), 82.0),
    "Front": (unreal.Vector(0, 315, 175), unreal.Vector(0, -90, 155), 70.0),
    "Elevated": (unreal.Vector(650, 560, 520), unreal.Vector(0, 0, 120), 58.0),
    "SystemsWall": (unreal.Vector(0, -175, 205), unreal.Vector(0, 270, 150), 70.0),
}
actors = {actor.get_actor_label(): actor for actor in actors_api.get_all_level_actors()}
for name, (location, target, fov) in camera_specs.items():
    actor = actors.get(f"LB_MCR_V001_CAM_{name}")
    if actor is None:
        failures.append(f"missing camera {name}")
        continue
    actor.set_actor_label(f"LB_MCR_V002_CAM_{name}")
    actor.set_actor_location(location, False, False)
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location, target), False)
    actor.camera_component.set_editor_property("field_of_view", fov)
    actor.tags = [unreal.Name("LB.ControlRoom.v002"), unreal.Name(f"LB.ControlRoom.Camera.{name}"), unreal.Name("LB.Asset.CandidateNotPromoted")]

levels.save_current_level()
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)
payload = {
    "$schema": "cairnwell/audit/main-control-room-presentation-build-v002/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__CAMERA_AXIS_EXPOSURE_AND_UE_NATIVE_MATERIAL_SUCCESSOR_BUILT__VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__CONTROL_ROOM_V002_BUILD__NOT_PROMOTED",
    "source_map": BASE,
    "map": MAP,
    "material_count": len(materials),
    "mesh_count": len(mesh_paths),
    "camera_axis_correction": "Blender +Y maps to Unreal -Y; v002 cameras use mirrored Y positions and targets.",
    "screen_orientation_claim": "UNRESOLVED_UNTIL_FRESH_FRONT_AND_SEATED_VISUAL_INSPECTION",
    "promotion_authorized": False,
    "gameplay_wired": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "failures": failures, "audit": str(OUT)}, indent=2))

