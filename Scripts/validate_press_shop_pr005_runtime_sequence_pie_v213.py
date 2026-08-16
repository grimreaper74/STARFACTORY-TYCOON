"""Run exact native PR005 sequence gate on cumulative v213."""
from pathlib import Path
source = Path(__file__).with_name("validate_press_shop_pr005_runtime_sequence_pie_v205.py")
code = source.read_text(encoding="utf-8").replace("v205", "v213").replace("V205", "V213")
code = code.replace("PR005ReleaseArtCandidate_v213", "CumulativeReleaseCandidate_v213")
exec(compile(code, str(source) + "::v213", "exec"), {"__name__": "__main__", "__file__": str(source)})
