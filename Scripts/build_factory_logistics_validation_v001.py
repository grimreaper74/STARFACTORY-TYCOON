"""Build an isolated visual bay for the licensed logistics shortlist."""

import unreal


MAP = "/Game/LineBoss/Developer/Validation/LB_FactoryLogistics_Candidate_v001"
ROOT = "/Game/LineBoss/Vendor/FactoryEnvironment/Logistics/Meshes"
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
cube = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
concrete = unreal.load_asset("/Game/LineBoss/Materials/M_LB_FactoryConcrete")
charcoal = unreal.load_asset("/Game/LineBoss/Materials/M_LB_ShellCharcoal")
controlled_root = "/Game/LineBoss/Shared/Logistics/Candidate_v001/Materials"
forklift_body = unreal.load_asset(f"{controlled_root}/M_LB_Logistics_ForkliftBody_v001")
forklift_detail = unreal.load_asset(f"{controlled_root}/M_LB_Logistics_ForkliftDetail_v001")
stillage = unreal.load_asset(f"{controlled_root}/M_LB_Logistics_Stillage_v001")
pallet_blue = unreal.load_asset(f"{controlled_root}/M_LB_Logistics_PalletBlue_v001")
crate_yellow = unreal.load_asset(f"{controlled_root}/M_LB_Logistics_CrateYellow_v001")


def mesh_actor(label, name, location, rotation=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0), overrides=()):
    mesh = unreal.load_asset(f"{ROOT}/{name}")
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing logistics mesh {name}")
    actor = actors.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator(*rotation))
    actor.set_actor_label("LB_LOGISTICS_" + label)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    component.set_mobility(unreal.ComponentMobility.STATIC)
    component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    component.set_collision_profile_name(unreal.Name("BlockAll"))
    for index, material in enumerate(overrides):
        if material is not None:
            component.set_material(index, material)
    actor.tags = [unreal.Name("LB.Vendor.FactoryEnvironment"),
                  unreal.Name("LB.Asset.ValidationOnly"),
                  unreal.Name("LB.Asset.CandidateNotPromoted")]
    return actor


def primitive(label, location, size, material):
    actor = actors.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label("LB_LOGISTICS_" + label)
    actor.set_actor_scale3d(unreal.Vector(size[0] / 100.0, size[1] / 100.0, size[2] / 100.0))
    component = actor.static_mesh_component
    component.set_static_mesh(cube)
    if material:
        component.set_material(0, material)
    return actor


if unreal.EditorAssetLibrary.does_asset_exist(MAP):
    levels.load_level(MAP)
    for existing in list(actors.get_all_level_actors()):
        actors.destroy_actor(existing)
elif not levels.new_level(MAP):
    raise RuntimeError("Failed creating logistics validation map")

primitive("Floor", (0, 0, -8), (1700, 1150, 12), concrete)
primitive("BackWall", (0, -535, 280), (1700, 12, 580), charcoal)
mesh_actor("Forklift", "SM_ForkLift", (-300, -110, 172.8), (0.0, 0.0, 0.0), overrides=(forklift_body, forklift_detail))
mesh_actor("PalletCart", "SM_PalletCart", (275, -110, 63.5), (0.0, 0.0, 18.0), overrides=(stillage,))
mesh_actor("OpenStillage", "SM_PalletCart_PalletBox_open", (275, -110, 59.0), (0.0, 0.0, 18.0), overrides=(stillage,))
mesh_actor("PlasticPallet", "SM_PlasticPallet01", (370, 240, 10.0), (0.0, 0.0, -12.0), overrides=(pallet_blue,))
for index, (x, y, yaw) in enumerate(((335, 220, -12), (405, 220, -8), (370, 275, 4)), 1):
    mesh_actor(f"Crate_{index:02d}", "SM_AssemblyLineCrate01", (x, y, 30.0), (0.0, 0.0, yaw), overrides=(crate_yellow,))

key = actors.spawn_actor_from_class(unreal.RectLight, unreal.Vector(260, 500, 620), unreal.Rotator())
key.set_actor_label("LB_LOGISTICS_Key")
key.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    key.get_actor_location(), unreal.Vector(0, -80, 120)), False)
key.rect_light_component.set_editor_properties({
    "intensity": 1350.0, "attenuation_radius": 1900.0,
    "source_width": 500.0, "source_height": 330.0,
})
fill = actors.spawn_actor_from_class(unreal.RectLight, unreal.Vector(-650, 300, 380), unreal.Rotator())
fill.set_actor_label("LB_LOGISTICS_Fill")
fill.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    fill.get_actor_location(), unreal.Vector(-220, -100, 140)), False)
fill.rect_light_component.set_editor_properties({
    "intensity": 650.0, "attenuation_radius": 1700.0,
    "source_width": 320.0, "source_height": 260.0,
})

exposure = actors.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(), unreal.Rotator())
exposure.set_actor_label("LB_LOGISTICS_Exposure")
exposure.set_editor_properties({"unbound": True, "blend_weight": 1.0})
settings = exposure.settings
settings.set_editor_properties({
    "override_auto_exposure_method": True,
    "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
    "override_auto_exposure_min_brightness": True,
    "override_auto_exposure_max_brightness": True,
    "auto_exposure_min_brightness": 1.0, "auto_exposure_max_brightness": 1.0,
    "override_auto_exposure_bias": True, "auto_exposure_bias": -2.25,
})
exposure.settings = settings

camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(930, 930, 500), unreal.Rotator())
camera.set_actor_label("LB_CAM_FactoryLogistics_v001")
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    camera.get_actor_location(), unreal.Vector(0, -70, 135)), False)
camera.camera_component.set_editor_properties({
    "field_of_view": 47.0, "aspect_ratio": 16.0 / 9.0,
    "constrain_aspect_ratio": True,
})

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("Failed saving logistics validation map")
unreal.log("LINE_BOSS_FACTORY_LOGISTICS_VALIDATION_BUILD_PASS map=" + MAP)
