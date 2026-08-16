"""Run the exact v233 management gate against upper-hall roof child v235."""

from pathlib import Path


source = Path(__file__).with_name("validate_press_shop_playable_management_pie_v233.py")
code = source.read_text(encoding="utf-8").replace("v233", "v235").replace("V233", "V235")
exec(compile(code, str(source) + "::v235", "exec"), globals(), globals())
