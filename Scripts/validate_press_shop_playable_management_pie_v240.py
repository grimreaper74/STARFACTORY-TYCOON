"""Run the exact retained management gate against collision-owned child v240."""

from pathlib import Path


source = Path(__file__).with_name("validate_press_shop_playable_management_pie_v233.py")
code = source.read_text(encoding="utf-8").replace("v233", "v240").replace("V233", "V240")
exec(compile(code, str(source) + "::v240", "exec"), globals(), globals())

