"""Run the retained management gate against support-fleet child v254."""

from pathlib import Path

source = Path(__file__).with_name("validate_press_shop_playable_management_pie_v241.py")
code = source.read_text(encoding="utf-8").replace("v241", "v254").replace("V241", "V254")
exec(compile(code, str(source) + "::v254", "exec"), globals(), globals())
