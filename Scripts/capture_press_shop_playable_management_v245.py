"""Capture v245 through the retained whole-shop fixed-camera suite."""

from pathlib import Path


source = Path(__file__).with_name("capture_press_shop_playable_management_v242.py")
code = source.read_text(encoding="utf-8").replace("v242", "v245").replace("V242", "V245")
exec(compile(code, str(source) + "::v245", "exec"), globals(), globals())
