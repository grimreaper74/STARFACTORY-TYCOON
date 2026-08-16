"""Run the exact retained management gate against broad-roof-fill child v247."""

from pathlib import Path


source = Path(__file__).with_name("validate_press_shop_playable_management_pie_v242.py")
code = source.read_text(encoding="utf-8").replace("v242", "v247").replace("V242", "V247")
exec(compile(code, str(source) + "::v247", "exec"), globals(), globals())
