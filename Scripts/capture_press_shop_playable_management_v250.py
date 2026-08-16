"""Capture support-area child v250 through the retained fixed-camera suite."""

from pathlib import Path


source = Path(__file__).with_name("capture_press_shop_playable_management_v242.py")
code = source.read_text(encoding="utf-8").replace("v242", "v250").replace("V242", "V250")
exec(compile(code, str(source) + "::v250", "exec"), globals(), globals())
