"""Run PR010 navigation against exact v269."""
from pathlib import Path
source = Path(__file__).with_name("validate_press_shop_pr010_navigation_pie_v255.py")
code = source.read_text(encoding="utf-8").replace("v255", "v269").replace("V255", "V269")
exec(compile(code, str(source) + "::v269", "exec"), globals(), globals())
