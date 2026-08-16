"""Exact v019 static gate adapter with legacy-proxy and game-mode checks."""

from pathlib import Path

source = Path(__file__).resolve().parent / "audit_press_train_a_physical_static_v018.py"
code = source.read_text(encoding="utf-8").replace("v018", "v019").replace("V018", "V019")

needle = """authorities = [actor for actor in actors if isinstance(actor, unreal.LBPressTrainAStation)]
legacy_safety_volumes = []
"""
replacement = """authorities = [actor for actor in actors if isinstance(actor, unreal.LBPressTrainAStation)]
legacy_simple_proxies = [actor for actor in actors if \"LB.Collision.SimpleProxy\" in tags(actor)]
world_settings = unreal.EditorLevelLibrary.get_editor_world().get_world_settings()
game_mode = world_settings.get_editor_property(\"default_game_mode\")
game_mode_path = game_mode.get_path_name() if game_mode else None
legacy_safety_volumes = []
"""
if needle not in code:
    raise RuntimeError("v018 authority block changed; refusing v019 static adapter")
code = code.replace(needle, replacement, 1)

needle = 'if len(authorities) != 1: failures.append(f"expected one native authority, found {len(authorities)}")'
replacement = needle + '''
if legacy_simple_proxies: failures.append(f"legacy station-box proxies remain: {[actor.get_actor_label() for actor in legacy_simple_proxies]}")
if not game_mode_path or "LBControlRoomGameMode" not in game_mode_path:
    failures.append(f"standing-player game mode mismatch: {game_mode_path}")'''
if needle not in code:
    raise RuntimeError("v018 cardinality block changed; refusing v019 static adapter")
code = code.replace(needle, replacement, 1)

needle = '"nav_bounds_volume_count": len(nav_bounds), "native_authority_count": len(authorities),'
replacement = ('"nav_bounds_volume_count": len(nav_bounds), "native_authority_count": len(authorities), '
               '"legacy_simple_proxy_count": len(legacy_simple_proxies), '
               '"standing_player_game_mode": game_mode_path,')
if needle not in code:
    raise RuntimeError("v018 report block changed; refusing v019 static adapter")
code = code.replace(needle, replacement, 1)

exec(compile(code, str(source) + "::v019", "exec"), globals(), globals())
