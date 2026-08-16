"""Run the exact retained management gate against navigation-restored v241."""

from pathlib import Path


source = Path(__file__).with_name("validate_press_shop_playable_management_pie_v233.py")
code = source.read_text(encoding="utf-8").replace("v233", "v241").replace("V233", "V241")
exec(compile(code, str(source) + "::v241", "exec"), globals(), globals())

