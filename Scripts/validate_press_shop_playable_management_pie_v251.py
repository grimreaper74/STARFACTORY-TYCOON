"""Run the exact retained management gate against structured-support child v251."""

from pathlib import Path


source = Path(__file__).with_name("validate_press_shop_playable_management_pie_v241.py")
code = source.read_text(encoding="utf-8").replace("v241", "v251").replace("V241", "V251")
exec(compile(code, str(source) + "::v251", "exec"), globals(), globals())
