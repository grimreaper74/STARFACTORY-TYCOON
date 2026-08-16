"""Adapt the inherited v074 runtime-navigation gate to layered-material v076."""
from pathlib import Path
base = Path(__file__).with_name("validate_press_shop_pr004_navigation_pie_v074.py")
code = base.read_text(encoding="utf-8").replace("v074", "v076").replace("NativeRuntime", "LayeredMaterial")
exec(compile(code, str(base) + "::v076-adapter", "exec"), globals(), globals())
