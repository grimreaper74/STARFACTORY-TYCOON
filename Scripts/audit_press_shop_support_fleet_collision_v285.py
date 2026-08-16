"""Run whole support-fleet collision audit against v285."""
from pathlib import Path
source = Path(__file__).with_name("audit_press_shop_support_fleet_collision_v269.py")
code = source.read_text(encoding="utf-8").replace("v269", "v285").replace("V269", "V285")
exec(compile(code, str(source) + "::v285", "exec"), globals(), globals())
