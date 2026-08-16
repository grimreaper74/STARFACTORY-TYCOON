"""Run the management gate unchanged against lighting child v226."""

from pathlib import Path


source = Path(__file__).with_name("validate_press_shop_playable_management_pie_v225.py")
code = source.read_text(encoding="utf-8").replace("v225", "v226").replace("V225", "V226")
exec(compile(code, str(source) + "::v226", "exec"), globals(), globals())

