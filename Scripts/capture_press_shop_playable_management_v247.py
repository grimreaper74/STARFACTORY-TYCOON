"""Capture v247 through the retained whole-shop fixed-camera suite."""

from pathlib import Path


source = Path(__file__).with_name("capture_press_shop_playable_management_v242.py")
code = source.read_text(encoding="utf-8").replace("v242", "v247").replace("V242", "V247")
exec(compile(code, str(source) + "::v247", "exec"), globals(), globals())
