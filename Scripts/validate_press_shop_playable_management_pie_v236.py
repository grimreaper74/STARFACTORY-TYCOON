"""Run the exact retained management gate against train-readability child v236."""

from pathlib import Path


source = Path(__file__).with_name("validate_press_shop_playable_management_pie_v233.py")
code = source.read_text(encoding="utf-8").replace("v233", "v236").replace("V233", "V236")
exec(compile(code, str(source) + "::v236", "exec"), globals(), globals())
