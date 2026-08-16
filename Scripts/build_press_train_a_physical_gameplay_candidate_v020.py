"""Fresh v020 from retained v017; authored collision, standing operator and navigation."""

from pathlib import Path

source = Path(__file__).resolve().parent / "build_press_train_a_physical_gameplay_candidate_v018.py"
code = source.read_text(encoding="utf-8").replace("v018", "v020").replace("V018", "V020")

# The collision plan is validated source evidence, not a failed-map parent.
code = code.replace("press_train_a_collision_plan_v020.json", "press_train_a_collision_plan_v018.json")
code = code.replace("PASS__V020_AUTHORED_GEOMETRY_COLLISION_PLAN", "PASS__V018_AUTHORED_GEOMETRY_COLLISION_PLAN")

needle = '''all_actors = actors_api.get_all_level_actors()
for actor in all_actors:
'''
replacement = '''all_actors = actors_api.get_all_level_actors()
legacy_simple_proxies = [actor for actor in all_actors
                         if "LB.Collision.SimpleProxy" in tags(actor)
                         and any(value.startswith("LB.PressTrain.Stage.S") for value in tags(actor))]
if len(legacy_simple_proxies) != 7:
    raise RuntimeError(f"Expected seven inherited technical station-box proxies, found {len(legacy_simple_proxies)}")
legacy_proxy_rows = []
for actor in legacy_simple_proxies:
    origin, extent = actor.get_actor_bounds(False, False)
    legacy_proxy_rows.append({"actor": actor.get_actor_label(),
                              "origin_cm": [origin.x, origin.y, origin.z],
                              "extent_cm": [extent.x, extent.y, extent.z]})
actors_api.destroy_actors(legacy_simple_proxies)

game_mode_class = unreal.load_class(None, "/Script/LineBossCarFactory.LBControlRoomGameMode")
if game_mode_class is None:
    raise RuntimeError("Could not load standing-player LBControlRoomGameMode")
world = unreal.EditorLevelLibrary.get_editor_world()
world_settings = world.get_world_settings()
world_settings.set_editor_property("default_game_mode", game_mode_class)

nav_config = world_settings.get_editor_property("navigation_system_config")
if nav_config is None:
    nav_config = unreal.new_object(
        unreal.NavigationSystemModuleConfig,
        outer=world_settings,
        name="LB_PressTrainA_NavigationSystemConfig_v020",
    )
nav_config.set_editor_property("strictly_static", False)
nav_config.set_editor_property("auto_spawn_missing_nav_data", True)
nav_config.set_editor_property("spawn_nav_data_in_nav_bounds_level", True)
nav_config.set_editor_property(
    "navigation_system_class",
    unreal.SoftClassPath("/Script/NavigationSystem.NavigationSystemV1"),
)
world_settings.set_editor_property("navigation_system_config", nav_config)

for actor in list(actors_api.get_all_level_actors()):
    if actor.get_class().get_name() == "LBPressShopNavigationBootstrap":
        actors_api.destroy_actor(actor)
nav_bootstrap = actors_api.spawn_actor_from_class(
    unreal.LBPressShopNavigationBootstrap,
    unreal.Vector(0.0, 2250.0, 25.0),
    unreal.Rotator(),
)
if nav_bootstrap is None:
    raise RuntimeError("Could not spawn Train A navigation bootstrap")
nav_bootstrap.set_actor_label("CA_MW_PTA_NavigationBootstrap_v020")
add_tags(nav_bootstrap, "LB.PressTrain.TrainA.Navigation", "LB.Asset.Candidate.v020",
         "LB.Asset.CandidateNotPromoted")

unreal.SystemLibrary.execute_console_command(world, "RebuildNavigation")
for actor in actors_api.get_all_level_actors():
    if isinstance(actor, unreal.RecastNavMesh):
        actor.set_editor_property("runtime_generation", unreal.RuntimeGenerationType.DYNAMIC)
        actor.set_editor_property("can_be_main_nav_data", True)

all_actors = actors_api.get_all_level_actors()
for actor in all_actors:
'''
if needle not in code:
    raise RuntimeError("v018 all-actors block changed; refusing v020 adapter")
code = code.replace(needle, replacement, 1)

needle = '"native_authority_count": len(authorities), "protected_map_hashes": protected_hashes,'
replacement = ('"native_authority_count": len(authorities), '
               '"standing_player_game_mode": "/Script/LineBossCarFactory.LBControlRoomGameMode", '
               '"removed_legacy_simple_proxy_count": len(legacy_proxy_rows), '
               '"removed_legacy_simple_proxies": legacy_proxy_rows, '
               '"navigation_bootstrap": nav_bootstrap.get_actor_label(), '
               '"navigation_system_config": nav_config.get_path_name(), '
               '"navigation_system_class": str(nav_config.get_editor_property("navigation_system_class")), '
               '"recast_nav_mesh_count": len([actor for actor in actors_api.get_all_level_actors() '
               'if isinstance(actor, unreal.RecastNavMesh)]), '
               '"protected_map_hashes": protected_hashes,')
if needle not in code:
    raise RuntimeError("v018 report block changed; refusing v020 adapter")
code = code.replace(needle, replacement, 1)

exec(compile(code, str(source) + "::v020", "exec"), globals(), globals())
