"""Capture v230 through the retained fixed-camera suite."""

from pathlib import Path


source = Path(__file__).with_name("capture_press_shop_playable_management_v229.py")
code = source.read_text(encoding="utf-8").replace("v229", "v230").replace("V229", "V230")
exec(compile(code, str(source) + "::v230", "exec"), globals(), globals())
