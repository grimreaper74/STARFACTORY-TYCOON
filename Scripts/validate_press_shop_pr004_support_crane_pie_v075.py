"""Adapt the inherited v074 support-crane gate to isolated visual-cleanup v075."""
from pathlib import Path
base = Path(__file__).with_name("validate_press_shop_pr004_support_crane_pie_v074.py")
code = base.read_text(encoding="utf-8").replace("v074", "v075").replace("NativeRuntime", "VisualCleanup")
exec(compile(code, str(base) + "::v075-adapter", "exec"), globals(), globals())
