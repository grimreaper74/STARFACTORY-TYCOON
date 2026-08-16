"""Run the exact retained management gate against balanced-lighting child v246."""

from pathlib import Path


source = Path(__file__).with_name("validate_press_shop_playable_management_pie_v242.py")
code = source.read_text(encoding="utf-8").replace("v242", "v246").replace("V242", "V246")
exec(compile(code, str(source) + "::v246", "exec"), globals(), globals())
