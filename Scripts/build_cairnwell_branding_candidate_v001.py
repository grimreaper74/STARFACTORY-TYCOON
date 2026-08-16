"""Build isolated Cairnwell plate candidates on HMI v004 and PR-005 validation maps."""

from pathlib import Path
import json
import unreal

PROJECT = Path(unreal.Paths.project_dir())
SOURCE_DIR = PROJECT / "SourceAssets/Brand/Candidate_v001"
ASSET_DIR = "/Game/LineBoss/Brand/Cairnwell/Candidate_v001"
HMI_SOURCE_MAP = "/Game/LineBoss/Developer/Validation/LB_HMI04_ModelingValidation"
HMI_MAP = "/Game/LineBoss/Developer/Validation/LB_HMI04_CairnwellBranding_v001"
AUDIT = Path(unreal.Paths.project_saved_dir()) / "Audits/cairnwell_branding_candidate_v001.json"

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
asset_lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
mel = unreal.MaterialEditingLibrary


def ensure_map(source, destination):
    if not asset_lib.does_asset_exist(destination):
        if not asset_lib.duplicate_asset(source, destination):
            raise RuntimeError(f"Could not duplicate {source} to {destination}")


def import_texture(filename, asset_name):
    path = f"{ASSET_DIR}/{asset_name}"
    existing = asset_lib.load_asset(path)
    if existing is not None:
        return existing
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(SOURCE_DIR / filename))
    task.set_editor_property("destination_path", ASSET_DIR)
    task.set_editor_property("destination_name", asset_name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", False)
    task.set_editor_property("save", True)
    asset_tools.import_asset_tasks([task])
    texture = asset_lib.load_asset(path)
    if texture is None:
        raise RuntimeError(f"Texture import failed: {filename}")
    texture.set_editor_property("srgb", True)
    texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)
    asset_lib.save_loaded_asset(texture, only_if_is_dirty=False)
    return texture


def material_for(texture, asset_name):
    path = f"{ASSET_DIR}/{asset_name}"
    material = asset_lib.load_asset(path)
    if material is None:
        material = asset_tools.create_asset(asset_name, ASSET_DIR, unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(f"Could not create material {path}")
    mel.delete_all_material_expressions(material)
    sample = mel.create_material_expression(material, unreal.MaterialExpressionTextureSample, -420, -80)
    sample.set_editor_property("texture", texture)
    rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -420, 140)
    rough.set_editor_property("r", 0.42)
    metal = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -420, 230)
    metal.set_editor_property("r", 0.12)
    mel.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    material.set_editor_property("two_sided", True)
    mel.recompile_material(material)
    asset_lib.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def clean(prefix):
    for actor in actors.get_all_level_actors():
        if actor.get_actor_label().startswith(prefix):
            actors.destroy_actor(actor)


def plate(label, location, width_cm, height_cm, material):
    mesh = unreal.load_asset("/Engine/BasicShapes/Plane.Plane")
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, location)
    actor.set_actor_label(label)
    actor.set_actor_rotation(unreal.Rotator(roll=90.0, pitch=0.0, yaw=0.0), False)
    actor.set_actor_scale3d(unreal.Vector(width_cm / 100.0, height_cm / 100.0, 1.0))
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    component.set_static_mesh(mesh)
    component.set_material(0, material)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("cast_shadow", False)
    return actor


def camera(label, location, target):
    actor = actors.spawn_actor_from_class(unreal.CameraActor, location)
    actor.set_actor_label(label)
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location, target), False)
    component = actor.get_editor_property("camera_component")
    component.set_editor_property("field_of_view", 42.0)
    component.set_editor_property("post_process_blend_weight", 0.0)
    return actor


hmi_texture = import_texture("T_CAIRNWELL_HMI_SHARED_PLATFORM_PLATE_v001.png", "T_Cairnwell_HMI_SharedPlate_v001")
pr_texture = import_texture("T_CAIRNWELL_PR005_ASSET_PLATE_v001.png", "T_Cairnwell_PR005_AssetPlate_v001")
hmi_material = material_for(hmi_texture, "M_Cairnwell_HMI_SharedPlate_v001")
material_for(pr_texture, "M_Cairnwell_PR005_AssetPlate_v001")

current_map = unreal.EditorLevelLibrary.get_editor_world().get_path_name().split(".")[0]
if current_map != HMI_MAP:
    raise RuntimeError(f"Launch this script with {HMI_MAP}; current map is {current_map}")
clean("LB_BRAND_HMI01_")
plate("LB_BRAND_HMI01_CairnwellSharedPlate", unreal.Vector(0.0, 25.75, 71.5), 42.0, 12.6, hmi_material)
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if label == "LB_HMI04_Key":
        actor.get_editor_property("directional_light_component").set_editor_property("intensity", 0.65)
    elif label == "LB_HMI04_Fill":
        actor.get_editor_property("rect_light_component").set_editor_property("intensity", 120.0)
    elif label == "LB_HMI04_FixedExposure":
        actor.set_editor_property("blend_weight", 1.0)
        settings = actor.get_editor_property("settings")
        settings.set_editor_properties({
            "override_auto_exposure_method": True,
            "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
            "override_auto_exposure_min_brightness": True,
            "override_auto_exposure_max_brightness": True,
            "auto_exposure_min_brightness": 1.0,
            "auto_exposure_max_brightness": 1.0,
            "override_auto_exposure_bias": True,
            "auto_exposure_bias": -2.25,
        })
        actor.set_editor_property("settings", settings)
levels.save_current_level()
asset_lib.save_directory(ASSET_DIR, only_if_is_dirty=False, recursive=True)

AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "status": "PASS_CANDIDATE_NOT_PROMOTED",
    "authority": "Docs/BRAND_IDENTITY_AUTHORITY.md",
    "source_directory": str(SOURCE_DIR),
    "unreal_asset_directory": ASSET_DIR,
    "maps": [HMI_MAP],
    "plates": [
        {"id": "IND-HMI-001", "size_mm": [420, 126], "map": HMI_MAP},
    ],
    "promotion": False,
}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_CAIRNWELL_BRANDING_V001_PASS audit={AUDIT}")
