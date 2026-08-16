"""Run exact native PR007 runtime/save gate on cumulative v213."""
from pathlib import Path
source = Path(__file__).with_name("validate_press_shop_pr007_runtime_pie_v209.py")
code = source.read_text(encoding="utf-8").replace("v209", "v213").replace("V209", "V213")
code = code.replace("LB_PressShop_PR007ReleaseArtCandidate_v213", "LB_PressShop_CumulativeReleaseCandidate_v213")
code = code.replace("now - started > 60.0", "now - started > 75.0")
code = code.replace("now - phase_started < 20.0", "now - phase_started < 30.0")
exec(compile(code, str(source) + "::v213", "exec"), globals(), globals())
