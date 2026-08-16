"""Run the retained management authority gate unchanged against ergonomic child v228."""

from pathlib import Path


source = Path(__file__).with_name("validate_press_shop_playable_management_pie_v227.py")
code = source.read_text(encoding="utf-8").replace("v227", "v228").replace("V227", "V228")
exec(compile(code, str(source) + "::v228", "exec"), globals(), globals())
