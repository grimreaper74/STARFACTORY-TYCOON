"""Run the retained management authority gate unchanged against visual child v230."""

from pathlib import Path


source = Path(__file__).with_name("validate_press_shop_playable_management_pie_v228.py")
code = source.read_text(encoding="utf-8").replace("v228", "v230").replace("V228", "V230")
exec(compile(code, str(source) + "::v230", "exec"), globals(), globals())
