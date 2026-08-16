"""Adapt the proven v074 collision/navigation audit to calibrated-lighting v079."""
from pathlib import Path
base = Path(__file__).with_name("audit_press_shop_pr004_collision_navigation_v074.py")
code = base.read_text(encoding="utf-8").replace("v074", "v079").replace(
    "NativeRuntime", "CalibratedLighting")
exec(compile(code, str(base) + "::v079-adapter", "exec"), globals(), globals())
