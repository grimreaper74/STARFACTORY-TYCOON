"""Capture v192 using the proven v191 live PIE capture harness."""

from pathlib import Path


source = Path(__file__).with_name("capture_press_shop_pr003_pr004_whole_hall_runtime_v191.py")
code = source.read_text(encoding="utf-8").replace("v191", "v192").replace("V191", "V192")
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
