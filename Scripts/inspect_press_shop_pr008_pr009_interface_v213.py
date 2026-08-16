"""Measure exact PR008-to-PR009 interface on cumulative v213."""
from pathlib import Path
source = Path(__file__).with_name("inspect_press_shop_pr008_pr009_interface_v074.py")
code = source.read_text(encoding="utf-8")
code = code.replace("PR008NativeRuntimeCandidate_v074", "CumulativeReleaseCandidate_v213")
code = code.replace("v074", "v213").replace("V074", "V213")
exec(compile(code, str(source) + "::v213-cumulative", "exec"), globals(), globals())
