"""Run the support-fleet collision gate against exact successor v260."""
from pathlib import Path
source = Path(__file__).with_name("audit_press_shop_support_fleet_collision_v255.py")
code = source.read_text(encoding="utf-8").replace("v255", "v260").replace("V255", "V260")
exec(compile(code, str(source) + "::v260", "exec"), globals(), globals())
