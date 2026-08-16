"""Run the retained support-fleet collision gate against exact v269."""
from pathlib import Path
source = Path(__file__).with_name("audit_press_shop_support_fleet_collision_v260.py")
code = source.read_text(encoding="utf-8").replace("v260", "v269").replace("V260", "V269")
exec(compile(code, str(source) + "::v269", "exec"), globals(), globals())
