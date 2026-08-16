"""Adapt the proven v074 runtime-navigation gate to reflection-environment v078."""
from pathlib import Path
base = Path(__file__).with_name("validate_press_shop_pr004_navigation_pie_v074.py")
code = base.read_text(encoding="utf-8").replace("v074", "v078").replace(
    "NativeRuntime", "ReflectionEnvironment")
exec(compile(code, str(base) + "::v078-adapter", "exec"), globals(), globals())
