"""Run the exact retained management gate against roof-fill child v243."""

from pathlib import Path


source = Path(__file__).with_name("validate_press_shop_playable_management_pie_v242.py")
code = source.read_text(encoding="utf-8").replace("v242", "v243").replace("V242", "V243")
exec(compile(code, str(source) + "::v243", "exec"), globals(), globals())
