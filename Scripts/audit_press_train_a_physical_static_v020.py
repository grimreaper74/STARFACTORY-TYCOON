"""Exact v020 static gate with navigation-system and bootstrap checks."""

from pathlib import Path

source = Path(__file__).resolve().parent / "audit_press_train_a_physical_static_v019.py"
code = source.read_text(encoding="utf-8").replace("v019", "v020").replace("V019", "V020")

needle = '''game_mode_path = game_mode.get_path_name() if game_mode else None
legacy_safety_volumes = []
'''
replacement = '''game_mode_path = game_mode.get_path_name() if game_mode else None
nav_config = world_settings.get_editor_property("navigation_system_config")
nav_system_class = str(nav_config.get_editor_property("navigation_system_class")) if nav_config else None
nav_bootstraps = [actor for actor in actors if actor.get_class().get_name() == "LBPressShopNavigationBootstrap"]
recast_nav_meshes = [actor for actor in actors if isinstance(actor, unreal.RecastNavMesh)]
legacy_safety_volumes = []
'''
if needle not in code:
    raise RuntimeError("v019 world-settings block changed; refusing v020 static adapter")
code = code.replace(needle, replacement, 1)

needle = '''if not game_mode_path or "LBControlRoomGameMode" not in game_mode_path:
    failures.append(f"standing-player game mode mismatch: {game_mode_path}")'''
replacement = needle + '''
if nav_config is None or "NavigationSystemV1" not in str(nav_system_class):
    failures.append(f"navigation-system config mismatch: {nav_system_class}")
if len(nav_bootstraps) != 1:
    failures.append(f"expected one navigation bootstrap, found {len(nav_bootstraps)}")'''
if needle not in code:
    raise RuntimeError("v019 game-mode gate changed; refusing v020 static adapter")
code = code.replace(needle, replacement, 1)

needle = '''"standing_player_game_mode": game_mode_path,'''
replacement = '''"standing_player_game_mode": game_mode_path,
               "navigation_system_config": nav_config.get_path_name() if nav_config else None,
               "navigation_system_class": nav_system_class,
               "navigation_bootstrap_count": len(nav_bootstraps),
               "recast_nav_mesh_count": len(recast_nav_meshes),'''
if needle not in code:
    raise RuntimeError("v019 report block changed; refusing v020 static adapter")
code = code.replace(needle, replacement, 1)

exec(compile(code, str(source) + "::v020", "exec"), globals(), globals())
