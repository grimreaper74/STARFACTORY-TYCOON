"""Capture v227 through the retained corrected fixed-camera suite."""

from pathlib import Path


source = Path(__file__).with_name("capture_press_shop_playable_management_v226.py")
code = source.read_text(encoding="utf-8").replace("v226", "v227").replace("V226", "V227")
exec(compile(code, str(source) + "::v227", "exec"), globals(), globals())
