import unreal

# Candidate-only sky diagnostic. This runs only in the open-bay review map and
# changes no shared asset or protected source level.
EXPECTED_MAP_SUFFIX = "LB_PressShop_SteamOpenBay_v004"
world = unreal.EditorLevelLibrary.get_editor_world()
if world is None or not world.get_path_name().endswith(EXPECTED_MAP_SUFFIX):
    raise RuntimeError("Refusing sky probe outside " + EXPECTED_MAP_SUFFIX)

directional = []
skylights = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    if isinstance(actor, unreal.DirectionalLight):
        component = actor.light_component
        component.set_editor_property("atmosphere_sun_light", True)
        component.set_editor_property("atmosphere_sun_light_index", 0)
        actor.set_actor_rotation(unreal.Rotator(-38.0, -32.0, 0.0), False)
        directional.append(actor.get_actor_label())
    elif isinstance(actor, unreal.SkyLight):
        component = actor.light_component
        component.set_editor_property("real_time_capture", True)
        skylights.append(actor.get_actor_label())

if not directional or not skylights:
    raise RuntimeError("Expected existing directional and sky lights, got directional={} sky={}".format(directional, skylights))

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save candidate sky probe")
unreal.log("PRESS_SHOP_V004_SKY_PROBE_PASS directional={} skylights={}".format(directional, skylights))
