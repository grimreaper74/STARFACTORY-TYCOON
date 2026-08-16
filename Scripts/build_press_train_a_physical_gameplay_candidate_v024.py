"""Fresh v024 direct from v017 with verified UE 5.8 navigation reflection."""

from pathlib import Path

source = Path(__file__).resolve().parent / "build_press_train_a_physical_gameplay_candidate_v020.py"
code = source.read_text(encoding="utf-8").replace("v020", "v024").replace("V020", "V024")
needle = '''nav_config = world_settings.get_editor_property("navigation_system_config")
if nav_config is None:
    nav_config = unreal.new_object(
        unreal.NavigationSystemModuleConfig,'''
replacement = '''nav_config = world_settings.get_editor_property("navigation_system_config")
module_config_class = unreal.load_class(None, "/Script/NavigationSystem.NavigationSystemModuleConfig")
if module_config_class is None:
    raise RuntimeError("Could not load Unreal 5.8 NavigationSystemModuleConfig class")
if nav_config is None or nav_config.get_class().get_name() != "NavigationSystemModuleConfig":
    nav_config = unreal.new_object(
        module_config_class,'''
if needle not in code:
    raise RuntimeError("v020 navigation constructor changed; refusing v024 adapter")
code = code.replace(needle, replacement, 1)
code = code.replace('"strictly_static"', '"bStrictlyStatic"')
code = code.replace('"auto_spawn_missing_nav_data"', '"bAutoSpawnMissingNavData"')
code = code.replace('"spawn_nav_data_in_nav_bounds_level"', '"bSpawnNavDataInNavBoundsLevel"')
exec(compile(code, str(source) + "::v024", "exec"), globals(), globals())
