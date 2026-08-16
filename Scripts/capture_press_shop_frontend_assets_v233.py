"""Capture v233 through the inherited front-end fixed-camera suite."""

from pathlib import Path


source = Path(__file__).with_name("capture_press_shop_frontend_assets_v230.py")
code = source.read_text(encoding="utf-8").replace("v230", "v233").replace("V230", "V233")
exec(compile(code, str(source) + "::v233", "exec"), globals(), globals())
