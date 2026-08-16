"""Run the exact retained management gate against shell-tonal child v242."""

from pathlib import Path


source = Path(__file__).with_name("validate_press_shop_playable_management_pie_v241.py")
code = source.read_text(encoding="utf-8").replace("v241", "v242").replace("V241", "V242")
exec(compile(code, str(source) + "::v242", "exec"), globals(), globals())
