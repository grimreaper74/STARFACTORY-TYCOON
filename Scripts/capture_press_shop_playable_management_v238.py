"""Capture v238 through the retained whole-shop fixed-camera suite."""

from pathlib import Path


source = Path(__file__).with_name("capture_press_shop_playable_management_v233.py")
code = source.read_text(encoding="utf-8").replace("v233", "v238").replace("V233", "V238")
exec(compile(code, str(source) + "::v238", "exec"), globals(), globals())
