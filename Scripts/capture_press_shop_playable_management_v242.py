"""Capture v242 through the retained whole-shop fixed-camera suite."""

from pathlib import Path


source = Path(__file__).with_name("capture_press_shop_playable_management_v233.py")
code = source.read_text(encoding="utf-8").replace("v233", "v242").replace("V233", "V242")
exec(compile(code, str(source) + "::v242", "exec"), globals(), globals())
