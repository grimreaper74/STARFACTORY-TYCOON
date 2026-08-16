"""Corrected-map capture wrapper for PR005 v197."""

from pathlib import Path


source = Path(__file__).with_name("capture_press_shop_pr005_runtime_cage_infill_v196.py")
code = source.read_text(encoding="utf-8").replace("V196", "V197").replace("v196", "v197")
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
