"""Run the proven corrected whole-shop PR009 navigation proof against exact v300."""

from pathlib import Path

source = Path(__file__).with_name("validate_press_shop_pr009_integrated_navigation_pie_v288.py")
code = source.read_text(encoding="utf-8").replace("v288", "v300").replace("V288", "V300")
exec(compile(code, str(source) + "::v300", "exec"), globals(), globals())
