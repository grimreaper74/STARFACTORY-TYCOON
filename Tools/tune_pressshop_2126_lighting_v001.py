"""Brighten the native Unreal 2126 candidate for an honest camera review."""
import unreal

MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
TAG = unreal.Name("LB.PressShop.2126.LightingV001")
MATS = {
    "M_LB_PS2126_Floor": (0.095, 0.115, 0.130),
    "M_LB_PS2126_CairnwellGreen": (0.080, 0.285, 0.235),
    "M_LB_PS2126_SafetyYellow": (0.950, 0.700, 0.020),
    "M_LB_PS2126_WarmWhite": (0.940, 0.910, 0.800),
    "M_LB_PS2126_SteelGrey": (0.380, 0.430, 0.455),
    "M_LB_PS2126_FoundryCharcoal": (0.060, 0.070, 0.080),
    "M_LB_PS2126_PaintedPaleGreen": (0.240, 0.500, 0.380),
    "M_LB_PS2126_CreamLane": (0.950, 0.875, 0.640),
    "M_LB_PS2126_OpticalCyan": (0.050, 0.700, 1.000),
    "M_LB_PS2126_StatusRed": (0.780, 0.120, 0.080),
}

if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("PRESSSHOP_2126_LIGHT_FAIL: map did not load")
actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
if any(TAG in actor.tags for actor in actors):
    raise RuntimeError("PRESSSHOP_2126_LIGHT_FAIL: lighting tune already applied")

mel = unreal.MaterialEditingLibrary
for name, value in MATS.items():
    mat = unreal.load_asset("/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Materials/" + name)
    if not isinstance(mat, unreal.Material):
        raise RuntimeError("PRESSSHOP_2126_LIGHT_FAIL: material missing " + name)
    nodes = mel.get_material_expressions(mat)
    colour = next((node for node in nodes if isinstance(node, unreal.MaterialExpressionConstant3Vector)), None)
    if colour is None:
        raise RuntimeError("PRESSSHOP_2126_LIGHT_FAIL: no base colour node " + name)
    colour.set_editor_property("constant", unreal.LinearColor(value[0], value[1], value[2], 1.0))
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat, only_if_is_dirty=False)

for actor in actors:
    label = actor.get_actor_label()
    if label == "2126 | native skylight":
        actor.get_component_by_class(unreal.SkyLightComponent).set_editor_property("intensity", 3.5)
    elif label == "2126 | warm directional sun":
        actor.get_component_by_class(unreal.DirectionalLightComponent).set_editor_property("intensity", 18.0)
    elif label.startswith("2126 | native softbox"):
        actor.get_component_by_class(unreal.RectLightComponent).set_editor_property("intensity", 145000.0)

sky = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(0, 0, 0), unreal.Rotator())
sky.set_actor_label("2126 | native open-bay atmosphere")
sky.tags = [TAG]
fog = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(0, 0, 0), unreal.Rotator())
fog.set_actor_label("2126 | open-bay atmospheric depth")
fog.tags = [TAG]
fog_comp = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
fog_comp.set_editor_property("fog_density", 0.0015)

hero = unreal.Vector(-14600, -17600, 7900)
target = unreal.Vector(4600, 0, 2600)
dx, dy, dz = target.x - hero.x, target.y - hero.y, target.z - hero.z
flat = (dx * dx + dy * dy) ** 0.5
unreal.EditorLevelLibrary.set_level_viewport_camera_info(hero, unreal.Rotator(pitch=__import__('math').degrees(__import__('math').atan2(dz, flat)), yaw=__import__('math').degrees(__import__('math').atan2(dy, dx)), roll=0.0))
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("PRESSSHOP_2126_LIGHT_FAIL: map did not save")
unreal.log("PRESSSHOP_2126_LIGHT_PASS")
