"""Run the exact retained management gate against high-bay child v245."""

from pathlib import Path


source = Path(__file__).with_name("validate_press_shop_playable_management_pie_v242.py")
code = source.read_text(encoding="utf-8").replace("v242", "v245").replace("V242", "V245")
exec(compile(code, str(source) + "::v245", "exec"), globals(), globals())
