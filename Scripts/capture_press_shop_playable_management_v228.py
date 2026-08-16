"""Capture v228 through its closer control-room camera and inherited whole-shop cameras."""

from pathlib import Path


source = Path(__file__).with_name("capture_press_shop_playable_management_v227.py")
code = source.read_text(encoding="utf-8").replace("v227", "v228").replace("V227", "V228")
exec(compile(code, str(source) + "::v228", "exec"), globals(), globals())
