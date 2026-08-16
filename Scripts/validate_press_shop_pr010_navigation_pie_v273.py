"""Run PR010 navigation against retained native-dock candidate v273."""
from pathlib import Path
source = Path(__file__).with_name("validate_press_shop_pr010_navigation_pie_v255.py")
code = source.read_text(encoding="utf-8").replace("v255", "v273").replace("V255", "V273")
exec(compile(code, str(source) + "::v273", "exec"), globals(), globals())
