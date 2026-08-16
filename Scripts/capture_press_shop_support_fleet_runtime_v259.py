"""Capture one live-PIE single-berth or overview view from v259."""

from pathlib import Path


source = Path(__file__).with_name("capture_press_shop_support_fleet_runtime_v258.py")
code = source.read_text(encoding="utf-8").replace("v258", "v259").replace("V258", "V259")
exec(compile(code, str(source) + "::v259", "exec"), globals(), globals())
