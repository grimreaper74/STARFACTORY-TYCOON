"""Run the exact retained management gate against scaled broad-fill child v248."""

from pathlib import Path


source = Path(__file__).with_name("validate_press_shop_playable_management_pie_v242.py")
code = source.read_text(encoding="utf-8").replace("v242", "v248").replace("V242", "V248")
exec(compile(code, str(source) + "::v248", "exec"), globals(), globals())
