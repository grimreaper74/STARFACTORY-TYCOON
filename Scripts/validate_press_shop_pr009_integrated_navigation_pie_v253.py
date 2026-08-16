"""Run the retained whole-shop PR009 navigation proof against v253."""

from pathlib import Path


source = Path(__file__).with_name("validate_press_shop_pr009_integrated_navigation_pie_v241.py")
code = source.read_text(encoding="utf-8").replace("v241", "v253").replace("V241", "V253")
exec(compile(code, str(source) + "::v253", "exec"), globals(), globals())
