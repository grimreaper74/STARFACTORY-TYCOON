"""Exact v024 static gate including physical policy and runtime navigation."""

from pathlib import Path

source = Path(__file__).resolve().parent / "audit_press_train_a_physical_static_v018.py"
code = source.read_text(encoding="utf-8").replace("v018", "v024").replace("V018", "V024")

needle = '''authorities = [actor for actor in actors if isinstance(actor, unreal.LBPressTrainAStation)]
legacy_safety_volumes = []
'''
replacement = '''authorities = [actor for actor in actors if isinstance(actor, unreal.LBPressTrainAStation)]
legacy_simple_proxies = [actor for actor in actors if "LB.Collision.SimpleProxy" in tags(actor)]
world_settings = unreal.EditorLevelLibrary.get_editor_world().get_world_settings()
game_mode = world_settings.get_editor_property("default_game_mode")
game_mode_path = game_mode.get_path_name() if game_mode else None
nav_config = world_settings.get_editor_property("navigation_system_config")
nav_system_class = str(nav_config.get_editor_property("navigation_system_class")) if nav_config else None
nav_bootstraps = [actor for actor in actors if actor.get_class().get_name() == "LBPressShopNavigationBootstrap"]
recast_nav_meshes = [actor for actor in actors if isinstance(actor, unreal.RecastNavMesh)]
legacy_safety_volumes = []
'''
if needle not in code:
    raise RuntimeError("v018 authority block changed; refusing v024 static adapter")
code = code.replace(needle, replacement, 1)

needle = 'if len(authorities) != 1: failures.append(f"expected one native authority, found {len(authorities)}")'
replacement = needle + '''
if legacy_simple_proxies: failures.append(f"legacy station-box proxies remain: {[actor.get_actor_label() for actor in legacy_simple_proxies]}")
if not game_mode_path or "LBControlRoomGameMode" not in game_mode_path:
    failures.append(f"standing-player game mode mismatch: {game_mode_path}")
if nav_config is None or nav_config.get_class().get_name() != "NavigationSystemModuleConfig":
    failures.append(f"navigation-system config mismatch: {nav_config.get_class().get_name() if nav_config else None}")
if len(nav_bootstraps) != 1:
    failures.append(f"expected one navigation bootstrap, found {len(nav_bootstraps)}")
if len(recast_nav_meshes) != 1:
    failures.append(f"expected one RecastNavMesh, found {len(recast_nav_meshes)}")'''
if needle not in code:
    raise RuntimeError("v018 cardinality block changed; refusing v024 static adapter")
code = code.replace(needle, replacement, 1)

needle = '"nav_bounds_volume_count": len(nav_bounds), "native_authority_count": len(authorities),'
replacement = ('"nav_bounds_volume_count": len(nav_bounds), "native_authority_count": len(authorities), '
               '"legacy_simple_proxy_count": len(legacy_simple_proxies), '
               '"standing_player_game_mode": game_mode_path, '
               '"navigation_system_config": nav_config.get_path_name() if nav_config else None, '
               '"navigation_system_config_class": nav_config.get_class().get_name() if nav_config else None, '
               '"navigation_system_class": nav_system_class, '
               '"navigation_bootstrap_count": len(nav_bootstraps), '
               '"recast_nav_mesh_count": len(recast_nav_meshes),')
if needle not in code:
    raise RuntimeError("v018 report block changed; refusing v024 static adapter")
code = code.replace(needle, replacement, 1)

exec(compile(code, str(source) + "::v024", "exec"), globals(), globals())
