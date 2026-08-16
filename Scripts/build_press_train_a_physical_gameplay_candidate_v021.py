"""Fresh v021 direct from v017 using the Unreal 5.8 module navigation config."""

from pathlib import Path

source = Path(__file__).resolve().parent / "build_press_train_a_physical_gameplay_candidate_v020.py"
code = source.read_text(encoding="utf-8").replace("v020", "v021").replace("V020", "V021")
needle = '''if nav_config is None:
    nav_config = unreal.new_object('''
replacement = '''if nav_config is None or nav_config.get_class().get_name() != "NavigationSystemModuleConfig":
    nav_config = unreal.new_object('''
if needle not in code:
    raise RuntimeError("v020 navigation-config condition changed; refusing v021 adapter")
code = code.replace(needle, replacement, 1)
exec(compile(code, str(source) + "::v021", "exec"), globals(), globals())
