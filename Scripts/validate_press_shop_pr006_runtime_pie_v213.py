"""Run exact native PR006 runtime/save gate on cumulative v213."""
from pathlib import Path
source = Path(__file__).with_name("validate_press_shop_pr006_runtime_pie_v208.py")
code = source.read_text(encoding="utf-8").replace("v208", "v213").replace("V208", "V213")
code = code.replace("PR006ReleaseArtCandidate_v213", "CumulativeReleaseCandidate_v213")
exec(compile(code, str(source) + "::v213", "exec"), globals(), globals())
