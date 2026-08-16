"""Capture live-PIE fixed views of clean visual successor v256."""

from pathlib import Path

source = Path(__file__).with_name("capture_press_shop_support_fleet_runtime_v255.py")
code = source.read_text(encoding="utf-8").replace("v255", "v256").replace("V255", "V256")
exec(compile(code, str(source) + "::v256", "exec"), globals(), globals())
