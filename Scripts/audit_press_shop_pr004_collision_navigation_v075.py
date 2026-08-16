"""Adapt the inherited v074 collision/navigation audit to isolated visual-cleanup v075."""
from pathlib import Path
base = Path(__file__).with_name("audit_press_shop_pr004_collision_navigation_v074.py")
code = base.read_text(encoding="utf-8").replace("v074", "v075").replace("NativeRuntime", "VisualCleanup")
exec(compile(code, str(base) + "::v075-adapter", "exec"), globals(), globals())
