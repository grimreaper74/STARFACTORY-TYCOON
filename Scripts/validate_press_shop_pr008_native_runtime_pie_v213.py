"""Run exact native PR008 runtime gate on cumulative v213."""
from pathlib import Path
source = Path(__file__).with_name("validate_press_shop_pr008_native_runtime_pie_v074.py")
code = source.read_text(encoding="utf-8")
code = code.replace("PR008NativeRuntimeCandidate_v074", "CumulativeReleaseCandidate_v213")
code = code.replace("v074", "v213").replace("V074", "V213")
code = code.replace('"save_root_format": 7', '"save_root_format": 10')
code = code.replace('"station_save_version": 2', '"station_save_version": 3')
code = code.replace("stable.version != 2", "stable.version != 3")
exec(compile(code, str(source) + "::v213-cumulative", "exec"), globals(), globals())
