"""Capture v229 through the retained fixed-camera suite."""

from pathlib import Path


source = Path(__file__).with_name("capture_press_shop_playable_management_v228.py")
code = source.read_text(encoding="utf-8").replace("v228", "v229").replace("V228", "V229")
exec(compile(code, str(source) + "::v229", "exec"), globals(), globals())
