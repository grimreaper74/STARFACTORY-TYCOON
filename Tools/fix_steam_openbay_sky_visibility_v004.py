import unreal

# Candidate-only recovery: the visual-only sky sphere currently occludes the
# editor cameras.  Hide it for review without changing any shared asset,
# protected map, or press actor.
EXPECTED_MAP_SUFFIX = "LB_PressShop_SteamOpenBay_v004"
SKY_LABEL = "Open-bay 2126 stylized sky field"

world = unreal.EditorLevelLibrary.get_editor_world()
if world is None or not world.get_path_name().endswith(EXPECTED_MAP_SUFFIX):
    raise RuntimeError("Refusing sky recovery outside " + EXPECTED_MAP_SUFFIX)

sky = next(
    (actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()
     if actor.get_actor_label() == SKY_LABEL),
    None,
)
if sky is None:
    raise RuntimeError("Candidate sky actor not found: " + SKY_LABEL)

sky.set_actor_hidden_in_game(True)
for component in sky.get_components_by_class(unreal.PrimitiveComponent):
    component.set_visibility(False, True)
    component.set_hidden_in_game(True, True)

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save sky recovery in candidate map")

unreal.log("PRESS_SHOP_V004_SKY_RECOVERY_PASS: hidden visual-only actor '{}'".format(SKY_LABEL))
