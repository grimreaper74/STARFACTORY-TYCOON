"""Build a contained visual A/B bay for the curated Factory Environment kit."""

import unreal


MAP = "/Game/LineBoss/Developer/Validation/LB_FactoryPack_KitValidation"
ROOT = "/Game/LineBoss/Vendor/FactoryEnvironment"

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
cube = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
concrete = unreal.load_asset("/Game/LineBoss/Materials/M_LB_FactoryConcrete")
charcoal = unreal.load_asset("/Game/LineBoss/Materials/M_LB_ShellCharcoal")


def mesh_actor(label, path, location, rotation=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0)):
    mesh = unreal.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing curated mesh {path}")
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator(*rotation))
    actor.set_actor_label("LB_VENDOR_" + label)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    component = actor.get_editor_property("static_mesh_component")
    component.set_static_mesh(mesh)
    component.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
    actor.set_editor_property("tags", [unreal.Name("LB.Vendor.FactoryEnvironment"), unreal.Name("LB.Asset.ValidationOnly")])
    return actor


def primitive(label, location, size, material):
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label("LB_VENDOR_" + label)
    actor.set_actor_scale3d(unreal.Vector(size[0] / 100.0, size[1] / 100.0, size[2] / 100.0))
    component = actor.get_editor_property("static_mesh_component")
    component.set_static_mesh(cube)
    if material:
        component.set_material(0, material)
    return actor


if unreal.EditorAssetLibrary.does_asset_exist(MAP):
    levels.load_level(MAP)
    for existing in actors.get_all_level_actors():
        actors.destroy_actor(existing)
elif not levels.new_level(MAP):
    raise RuntimeError("Failed to create Factory Environment validation map")

primitive("Floor", (0, 0, -8), (1500, 1000, 12), concrete)
primitive("BackWall", (0, -470, 260), (1500, 12, 540), charcoal)

# Structural and access kit.
mesh_actor("Platform", f"{ROOT}/Meshes/SM_IndustrialPlatform01", (-260, -150, 0))
mesh_actor("Railing", f"{ROOT}/Meshes/SM_PlatformRailing_01", (-260, 5, 70), (0, 0, 90))
mesh_actor("FenceA", f"{ROOT}/Meshes/SM_Fence_01", (120, -40, 50), (0, 0, 90), (1.6, 1.6, 1.6))
mesh_actor("FencePost", f"{ROOT}/Meshes/SM_FencePart_01", (18, -40, 57), (0, 0, 90), (1.6, 1.6, 1.6))
mesh_actor("Column", f"{ROOT}/Meshes/SM_Column_02", (430, -240, 250))
mesh_actor("Beam", f"{ROOT}/Meshes/SM_MetalBeam01", (0, -310, 430), (0, 0, 90), (1.3, 1.0, 1.0))

# Service routing and believable machine dressing.
mesh_actor("PipeLongA", f"{ROOT}/Meshes/SM_Pipe_round_long", (-40, -325, 300), (0, 0, 90), (1.8, 1.8, 1.8))
mesh_actor("PipeCorner", f"{ROOT}/Meshes/SM_Pipe_round_corner1", (140, -325, 300), (0, 0, 90), (1.8, 1.8, 1.8))
mesh_actor("PipeTee", f"{ROOT}/Meshes/SM_Pipe_round_tee_transition1", (230, -325, 300), (0, 0, 90), (1.8, 1.8, 1.8))
mesh_actor("PipeClamp", f"{ROOT}/Meshes/SM_Pipe_round_fixator", (40, -325, 300), (0, 0, 90), (1.8, 1.8, 1.8))
mesh_actor("CableRun", f"{ROOT}/Meshes/SM_Cables01", (-300, -305, 220), (0, 0, 90))
mesh_actor("CableBundle", f"{ROOT}/Meshes/SM_CableSet_01", (50, 120, 35), (0, 0, 90), (1.8, 1.8, 1.8))
mesh_actor("ElectricalCable", f"{ROOT}/Meshes/SM_ElectricalCable_01", (310, 90, 35), (0, 90, 0), (1.3, 1.3, 1.3))
mesh_actor("Motor", f"{ROOT}/Meshes/Crane/SM_ElectricMotor01", (-260, -150, 100), (0, 0, 90), (0.75, 0.75, 0.75))
mesh_actor("Lamp", f"{ROOT}/Meshes/SM_Lamp01", (430, -230, 450), (0, 0, 0), (1.8, 1.8, 1.8))

key = actors.spawn_actor_from_class(unreal.RectLight, unreal.Vector(230, 320, 520), unreal.Rotator())
key.set_actor_label("LB_VENDOR_Key")
key.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(key.get_actor_location(), unreal.Vector(0, -70, 150)), False)
key.get_editor_property("rect_light_component").set_editor_properties({
    "intensity": 1100.0,
    "attenuation_radius": 1800.0,
    "source_width": 450.0,
    "source_height": 300.0,
})
fill = actors.spawn_actor_from_class(unreal.RectLight, unreal.Vector(-500, 220, 300), unreal.Rotator())
fill.set_actor_label("LB_VENDOR_Fill")
fill.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(fill.get_actor_location(), unreal.Vector(-100, -80, 120)), False)
fill.get_editor_property("rect_light_component").set_editor_properties({
    "intensity": 500.0,
    "attenuation_radius": 1600.0,
    "source_width": 300.0,
    "source_height": 250.0,
})

# Lock exposure for deterministic A/B captures.  The default auto exposure made
# pale vendor materials clip to white in unattended screenshots and hid their
# roughness/normal response.
exposure = actors.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(), unreal.Rotator())
exposure.set_actor_label("LB_VENDOR_Exposure")
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
    "auto_exposure_bias": -2.75,
})
exposure.set_editor_property("settings", settings)

camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(850, 900, 520), unreal.Rotator())
camera.set_actor_label("LB_CAM_FactoryPack_Kit")
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(0, -100, 150)), False)
camera.get_editor_property("camera_component").set_editor_property("field_of_view", 48.0)

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("Failed saving Factory Environment validation map")
unreal.log("LINE_BOSS_FACTORY_PACK_VALIDATION_BUILD_PASS assets=15 map=" + MAP)
