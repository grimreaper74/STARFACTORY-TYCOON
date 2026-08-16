"""Run the retained whole-shop PR009 navigation proof against v255."""

from pathlib import Path

source = Path(__file__).with_name("validate_press_shop_pr009_integrated_navigation_pie_v241.py")
code = source.read_text(encoding="utf-8").replace("v241", "v255").replace("V241", "V255")
exec(compile(code, str(source) + "::v255", "exec"), globals(), globals())
