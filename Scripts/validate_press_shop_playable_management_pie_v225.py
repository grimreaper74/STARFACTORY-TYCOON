"""Run the v222 management gate unchanged against corrected v225."""

from pathlib import Path


source = Path(__file__).with_name("validate_press_shop_playable_management_pie_v222.py")
code = source.read_text(encoding="utf-8")
code = code.replace("v222", "v225").replace("V222", "V225")
exec(compile(code, str(source) + "::v225", "exec"), globals(), globals())

