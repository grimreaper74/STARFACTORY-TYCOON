"""Run the PR010 navigation PIE gate against exact successor v259."""
from pathlib import Path
source = Path(__file__).with_name("validate_press_shop_pr010_navigation_pie_v255.py")
code = source.read_text(encoding="utf-8").replace("v255", "v259").replace("V255", "V259")
exec(compile(code, str(source) + "::v259", "exec"), globals(), globals())
