"""Run PR009 integrated navigation against complete-cell v285."""
from pathlib import Path
source = Path(__file__).with_name("validate_press_shop_pr009_integrated_navigation_pie_v273.py")
code = source.read_text(encoding="utf-8").replace("v273", "v285").replace("V273", "V285")
exec(compile(code, str(source) + "::v285", "exec"), globals(), globals())
