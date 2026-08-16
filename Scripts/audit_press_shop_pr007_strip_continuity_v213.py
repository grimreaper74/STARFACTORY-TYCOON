"""Measure inherited PR007 strip/bridge continuity on cumulative v213."""
from pathlib import Path
source = Path(__file__).with_name("audit_press_shop_pr007_strip_continuity_v209.py")
code = source.read_text(encoding="utf-8").replace("v209", "v213").replace("V209", "V213")
code = code.replace("PR007ReleaseArtCandidate_v213", "CumulativeReleaseCandidate_v213")
exec(compile(code, str(source) + "::v213", "exec"), globals(), globals())
