"""Run the exact retained management gate against balanced-support child v253."""

from pathlib import Path


source = Path(__file__).with_name("validate_press_shop_playable_management_pie_v241.py")
code = source.read_text(encoding="utf-8").replace("v241", "v253").replace("V241", "V253")
exec(compile(code, str(source) + "::v253", "exec"), globals(), globals())
