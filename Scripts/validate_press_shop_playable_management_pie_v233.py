"""Run the exact v230 management gate against shell-readability child v233."""

from pathlib import Path


source = Path(__file__).with_name("validate_press_shop_playable_management_pie_v230.py")
code = source.read_text(encoding="utf-8").replace("v230", "v233").replace("V230", "V233")
exec(compile(code, str(source) + "::v233", "exec"), globals(), globals())
