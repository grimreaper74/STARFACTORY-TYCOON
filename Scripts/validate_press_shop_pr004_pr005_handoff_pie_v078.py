"""Adapt the proven v074 traceable handoff gate to reflection-environment v078."""
from pathlib import Path
base = Path(__file__).with_name("validate_press_shop_pr004_pr005_handoff_pie_v074.py")
code = base.read_text(encoding="utf-8").replace("v074", "v078").replace(
    "NativeRuntime", "ReflectionEnvironment")
exec(compile(code, str(base) + "::v078-adapter", "exec"), globals(), globals())
