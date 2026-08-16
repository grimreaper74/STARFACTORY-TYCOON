"""Adapt the inherited v074 support-crane gate to smooth-layer v077."""
from pathlib import Path
base = Path(__file__).with_name("validate_press_shop_pr004_support_crane_pie_v074.py")
code = base.read_text(encoding="utf-8").replace("v074", "v077").replace("NativeRuntime", "SmoothLayer")
exec(compile(code, str(base) + "::v077-adapter", "exec"), globals(), globals())
