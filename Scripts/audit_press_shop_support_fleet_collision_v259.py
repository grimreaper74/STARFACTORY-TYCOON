"""Run the v255 support-fleet collision gate against exact successor v259."""
from pathlib import Path
source = Path(__file__).with_name("audit_press_shop_support_fleet_collision_v255.py")
code = source.read_text(encoding="utf-8").replace("v255", "v259").replace("V255", "V259")
exec(compile(code, str(source) + "::v259", "exec"), globals(), globals())
