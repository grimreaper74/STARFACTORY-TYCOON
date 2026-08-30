import math
import unreal

# Native-Unreal presentation refinement for the roofless v004 candidate. It
# adds a stylised open-sky field and replaces only candidate camera transforms.
# No Meshy asset, source map, roof surface, or shared material is touched.
EXPECTED_MAP_SUFFIX = "LB_PressShop_SteamOpenBay_v004"
ROOT = "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001"
MATERIAL_PATH = ROOT + "/Materials/M_LB_PS_OpenSkyField_v004"
SKY_LABEL = "Open-bay 2126 stylized sky field"
TAG = unreal.Name("LB.PressShop.SteamOpenBay.v004")
VISUAL_TAG = unreal.Name("LB.Environment.VisualOnly")


def aim(source, target):
    delta = target - source
    horizontal = (delta.x * delta.x + delta.y * delta.y) ** 0.5
    return unreal.Rotator(
        pitch=math.degrees(math.atan2(delta.z, horizontal)),
        yaw=math.degrees(math.atan2(delta.y, delta.x)),
        roll=0.0,
    )


world = unreal.EditorLevelLibrary.get_editor_world()
if world is None or not world.get_path_name().endswith(EXPECTED_MAP_SUFFIX):
    raise RuntimeError("Refusing presentation refinement outside " + EXPECTED_MAP_SUFFIX)

actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
if any(actor.get_actor_label() == SKY_LABEL for actor in actors):
    raise RuntimeError("Sky field already exists; refusing duplicate candidate dressing")

sky_material = unreal.load_asset(MATERIAL_PATH)
if sky_material is None:
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    sky_material = asset_tools.create_asset(
        "M_LB_PS_OpenSkyField_v004",
        ROOT + "/Materials",
        unreal.Material,
        unreal.MaterialFactoryNew(),
    )
    if sky_material is None:
        raise RuntimeError("Could not create candidate sky material")
    sky_material.set_editor_property("two_sided", True)
    sky_material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    editing = unreal.MaterialEditingLibrary
    colour = editing.create_material_expression(sky_material, unreal.MaterialExpressionConstant3Vector, -240, 0)
    # A quiet blue-teal open sky: clear enough to replace void black, subdued
    # enough that the green/yellow press language remains the hero.
    colour.set_editor_property("constant", unreal.LinearColor(0.055, 0.12, 0.20, 1.0))
    editing.connect_material_property(colour, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    editing.recompile_material(sky_material)
    unreal.EditorAssetLibrary.save_loaded_asset(sky_material, only_if_is_dirty=False)

sphere = unreal.load_asset("/Engine/BasicShapes/Sphere")
if sphere is None:
    raise RuntimeError("Native Unreal sphere mesh unavailable")
sky = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(7000.0, 0.0, 5000.0))
if sky is None:
    raise RuntimeError("Could not spawn candidate sky field")
sky.set_actor_label(SKY_LABEL)
sky.tags = [TAG, VISUAL_TAG, unreal.Name("LB.PressShop.OpenSky")]
component = sky.static_mesh_component
component.set_static_mesh(sphere)
component.set_material(0, sky_material)
component.set_world_scale3d(unreal.Vector(700.0, 700.0, 700.0))
component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
component.set_cast_shadow(False)

camera_updates = {
    "Steam wishlist full-process overview": (
        unreal.Vector(4300.0, -6400.0, 1650.0),
        unreal.Vector(5100.0, 0.0, 400.0),
        53.0,
    ),
    "Steam wishlist press-line hero": (
        unreal.Vector(10100.0, -4400.0, 1350.0),
        unreal.Vector(10300.0, 0.0, 440.0),
        44.0,
    ),
}
for label, (location, target, field_of_view) in camera_updates.items():
    camera = next((actor for actor in actors if actor.get_actor_label() == label), None)
    if camera is None or not isinstance(camera, unreal.CameraActor):
        raise RuntimeError("Expected review camera missing: " + label)
    camera.set_actor_location(location, False, False)
    camera.set_actor_rotation(aim(location, target), False)
    camera.camera_component.set_editor_property("field_of_view", field_of_view)

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate presentation refinement")
unreal.log("PRESS_SHOP_V004_PRESENTATION_REFINEMENT_PASS sky={} cameras={}".format(SKY_LABEL, list(camera_updates)))
