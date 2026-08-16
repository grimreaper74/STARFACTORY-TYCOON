"""Run retained control-room support-fleet authority cycle against v273."""
from pathlib import Path
source = Path(__file__).with_name("validate_press_shop_control_room_support_fleet_pie_v269.py")
code = source.read_text(encoding="utf-8").replace("v269", "v273").replace("V269", "V273")
exec(compile(code, str(source) + "::v273", "exec"), globals(), globals())
