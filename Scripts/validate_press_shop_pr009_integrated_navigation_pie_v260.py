"""Run the PR009 navigation PIE gate against exact successor v260."""
from pathlib import Path
source = Path(__file__).with_name("validate_press_shop_pr009_integrated_navigation_pie_v255.py")
code = source.read_text(encoding="utf-8").replace("v255", "v260").replace("V255", "V260")
exec(compile(code, str(source) + "::v260", "exec"), globals(), globals())
