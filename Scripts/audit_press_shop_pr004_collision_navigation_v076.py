"""Adapt the inherited v074 collision/navigation audit to layered-material v076."""
from pathlib import Path
base = Path(__file__).with_name("audit_press_shop_pr004_collision_navigation_v074.py")
code = base.read_text(encoding="utf-8").replace("v074", "v076").replace("NativeRuntime", "LayeredMaterial")
exec(compile(code, str(base) + "::v076-adapter", "exec"), globals(), globals())
