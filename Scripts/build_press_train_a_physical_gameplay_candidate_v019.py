"""Fresh v019 from retained v017; replace crude station boxes and enable the standing operator."""

from pathlib import Path

source = Path(__file__).resolve().parent / "build_press_train_a_physical_gameplay_candidate_v018.py"
code = source.read_text(encoding="utf-8").replace("v018", "v019").replace("V018", "V019")

# The collision plan is validated source evidence, not a failed map parent.  Reuse
# it unchanged while building the new map directly from retained v017.
code = code.replace("press_train_a_collision_plan_v019.json", "press_train_a_collision_plan_v018.json")
code = code.replace("PASS__V019_AUTHORED_GEOMETRY_COLLISION_PLAN", "PASS__V018_AUTHORED_GEOMETRY_COLLISION_PLAN")

needle = """all_actors = actors_api.get_all_level_actors()
for actor in all_actors:
"""
replacement = """all_actors = actors_api.get_all_level_actors()
legacy_simple_proxies = [actor for actor in all_actors
                         if \"LB.Collision.SimpleProxy\" in tags(actor)
                         and any(value.startswith(\"LB.PressTrain.Stage.S\") for value in tags(actor))]
if len(legacy_simple_proxies) != 7:
    raise RuntimeError(f\"Expected seven inherited technical station-box proxies, found {len(legacy_simple_proxies)}\")
legacy_proxy_rows = []
for actor in legacy_simple_proxies:
    origin, extent = actor.get_actor_bounds(False, False)
    legacy_proxy_rows.append({\"actor\": actor.get_actor_label(),
                              \"origin_cm\": [origin.x, origin.y, origin.z],
                              \"extent_cm\": [extent.x, extent.y, extent.z]})
actors_api.destroy_actors(legacy_simple_proxies)

game_mode_class = unreal.load_class(None, \"/Script/LineBossCarFactory.LBControlRoomGameMode\")
if game_mode_class is None:
    raise RuntimeError(\"Could not load standing-player LBControlRoomGameMode\")
world = unreal.EditorLevelLibrary.get_editor_world()
world.get_world_settings().set_editor_property(\"default_game_mode\", game_mode_class)

all_actors = actors_api.get_all_level_actors()
for actor in all_actors:
"""
if needle not in code:
    raise RuntimeError("v018 all-actors block changed; refusing unverified v019 adapter")
code = code.replace(needle, replacement, 1)

needle = '"native_authority_count": len(authorities), "protected_map_hashes": protected_hashes,'
replacement = ('"native_authority_count": len(authorities), '
               '"standing_player_game_mode": "/Script/LineBossCarFactory.LBControlRoomGameMode", '
               '"removed_legacy_simple_proxy_count": len(legacy_proxy_rows), '
               '"removed_legacy_simple_proxies": legacy_proxy_rows, '
               '"protected_map_hashes": protected_hashes,')
if needle not in code:
    raise RuntimeError("v018 report block changed; refusing unverified v019 adapter")
code = code.replace(needle, replacement, 1)

exec(compile(code, str(source) + "::v019", "exec"), globals(), globals())
