"""Run the exact retained management gate against structured-support child v252."""

from pathlib import Path


source = Path(__file__).with_name("validate_press_shop_playable_management_pie_v241.py")
code = source.read_text(encoding="utf-8").replace("v241", "v252").replace("V241", "V252")
exec(compile(code, str(source) + "::v252", "exec"), globals(), globals())
