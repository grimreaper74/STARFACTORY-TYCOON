"""Capture live-PIE fixed views of corrected visual successor v257."""

from pathlib import Path

source = Path(__file__).with_name("capture_press_shop_support_fleet_runtime_v255.py")
code = source.read_text(encoding="utf-8").replace("v255", "v257").replace("V255", "V257")
exec(compile(code, str(source) + "::v257", "exec"), globals(), globals())
