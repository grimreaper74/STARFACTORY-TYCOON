"""Capture one live-PIE single-berth or overview view from v260."""

from pathlib import Path


source = Path(__file__).with_name("capture_press_shop_support_fleet_runtime_v259.py")
code = source.read_text(encoding="utf-8").replace("v259", "v260").replace("V259", "V260")
exec(compile(code, str(source) + "::v260", "exec"), globals(), globals())
