"""Build a fresh isolated v504 inbound presentation; never modifies retained v438."""
import unreal

MAP = "/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryPresentation_v504"
DEST = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v003"
BRIDGE = "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary

if library.does_asset_exist(MAP):
    raise RuntimeError(f"Refusing overwrite {MAP}")
if not levels.new_level(MAP):
    raise RuntimeError("Could not create v504")

def add(label, path, loc, rot=(0, 0, 0), scale=(1, 1, 1), tags=()):
    mesh = library.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing {path}")
    actor = actors.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*loc), unreal.Rotator(*rot)
    )
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.tags = [
        unreal.Name("LB.Asset.ValidationOnly"),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
    ] + [unreal.Name(tag) for tag in tags]
    return actor

def mod(name, loc, rot=(0, 0, 0)):
    return add(
        "LB_INBOUND_V004_" + name,
        f"{DEST}/SM_CA_MW_MOD_{name}_v003",
        loc,
        rot,
    )

# v503 proved that the third positional Rotator field is yaw for these scripts.
mod("LorryCab", (0, -885, 152), rot=(0, 0, 180))
mod("CoilTrailer", (0, -150, 188))
mod("DockGuidesAndRestraint", (0, -150, 35))
mod("EntranceDockEnvelope", (0, -665, 244))
mod("DockControlAndSignals", (-310, -500, 125))
mod("CraneBayStructure", (0, 700, 320))
mod("ReceivingSaddle", (0, 700, 47))
mod("IdentityScanner", (240, 700, 93))
mod("AGVHandoffGuides", (420, 850, 18))

add(
    "LB_INBOUND_V004_AGV_Chassis",
    "/Game/LineBoss/IndustrialKit/MaterialHandling/CoilAGV/Candidate_v001/SM_LB_CoilAGV_Chassis_Candidate_v001",
    (420, 850, 45),
    tags=("LB.Vehicle.CoilAGV",),
)
add(
    "LB_INBOUND_V004_AGV_Deck",
    "/Game/LineBoss/IndustrialKit/MaterialHandling/CoilAGV/Candidate_v001/SM_LB_CoilAGV_LiftDeck_Candidate_v001",
    (420, 850, 83),
    tags=("LB.Vehicle.CoilAGV.LiftDeck",),
)

yellow = library.load_asset(
    "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_SafetyYellow_v001"
)
girder = add(
    "LB_INBOUND_V004_CraneGirder",
    f"{BRIDGE}/SM_LB_Crane_BridgeGirder_4500_v001",
    (0, 700, 610),
    scale=(1.42, 1, 1),
)
trolley = add(
    "LB_INBOUND_V004_CraneTrolley",
    f"{BRIDGE}/SM_LB_Crane_Trolley_v001",
    (0, 500, 625),
)
hoist = add(
    "LB_INBOUND_V004_HoistBlock",
    f"{BRIDGE}/SM_LB_Crane_HoistBlock_v001",
    (0, 500, 500),
)
hook = add(
    "LB_INBOUND_V004_PoweredCHook",
    f"{BRIDGE}/PoweredCHook/Candidate_v035/SM_LB_Crane_PoweredCHook_Candidate_v035",
    (0, 500, 315),
    rot=(0, 0, 90),
)
for crane_actor in (girder, trolley, hoist, hook):
    for index in range(crane_actor.static_mesh_component.get_num_materials()):
        crane_actor.static_mesh_component.set_material(index, yellow)

floor = add(
    "LB_INBOUND_V004_Floor",
    "/Engine/BasicShapes/Cube.Cube",
    (0, 100, -12),
    scale=(18, 28, .24),
    tags=("LB.Environment.ReviewOnly",),
)
floor.static_mesh_component.set_material(
    0, library.load_asset("/Game/LineBoss/Materials/M_LB_FactoryConcrete")
)
steel = library.load_asset(
    "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_BrushedSteel_v001"
)
charcoal = library.load_asset(
    "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_Charcoal_v001"
)
back = add(
    "LB_INBOUND_V004_Backdrop",
    "/Engine/BasicShapes/Cube.Cube",
    (0, 1650, 380),
    scale=(18, .18, 7.6),
    tags=("LB.Environment.ReviewOnly",),
)
back.static_mesh_component.set_material(0, steel)
for x in (-750, -375, 0, 375, 750):
    column = add(
        "LB_INBOUND_V004_BackdropColumn_" + str(x),
        "/Engine/BasicShapes/Cube.Cube",
        (x, 1550, 390),
        scale=(.18, .18, 7.8),
        tags=("LB.Environment.ReviewOnly",),
    )
    column.static_mesh_component.set_material(0, charcoal)

# Balanced review lighting: readable dark machinery without clipping safety yellow.
sun = actors.spawn_actor_from_class(
    unreal.DirectionalLight, unreal.Vector(), unreal.Rotator(-35, -25, -18)
)
sun.get_component_by_class(unreal.DirectionalLightComponent).set_editor_property(
    "intensity", 1.25
)
sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(), unreal.Rotator())
sky.get_component_by_class(unreal.SkyLightComponent).set_editor_properties(
    {"intensity": .8, "real_time_capture": True}
)
key = actors.spawn_actor_from_class(
    unreal.RectLight, unreal.Vector(-500, -200, 1050), unreal.Rotator()
)
key.set_actor_rotation(
    unreal.MathLibrary.find_look_at_rotation(
        key.get_actor_location(), unreal.Vector(0, 320, 180)
    ),
    False,
)
key.rect_light_component.set_editor_properties(
    {
        "intensity": 850.0,
        "attenuation_radius": 3500.0,
        "source_width": 1100.0,
        "source_height": 650.0,
    }
)

pp = actors.spawn_actor_from_class(
    unreal.PostProcessVolume, unreal.Vector(), unreal.Rotator()
)
pp.set_editor_properties({"unbound": True, "blend_weight": 1.0})
settings = pp.settings
settings.set_editor_properties(
    {
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True,
        "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0,
        "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True,
        "auto_exposure_bias": -1.35,
    }
)
pp.settings = settings

camera = actors.spawn_actor_from_class(
    unreal.CameraActor, unreal.Vector(-1750, -2200, 1025), unreal.Rotator()
)
camera.set_actor_label("LB_CAM_InboundCoilDelivery_Presentation_v504")
camera.set_actor_rotation(
    unreal.MathLibrary.find_look_at_rotation(
        camera.get_actor_location(), unreal.Vector(0, 300, 205)
    ),
    False,
)
camera.camera_component.set_editor_properties(
    {"field_of_view": 49.0, "aspect_ratio": 16 / 9, "constrain_aspect_ratio": True}
)
camera.tags = [unreal.Name("LB.Camera.Fixed"), unreal.Name("LB.Asset.ValidationOnly")]

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("Failed saving v504")
unreal.log("LINE_BOSS_INBOUND_PRESENTATION_V504_BUILD_PASS")
