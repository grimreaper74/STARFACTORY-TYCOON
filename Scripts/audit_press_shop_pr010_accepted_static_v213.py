"""Prove accepted PR010 scope remains inherited by cumulative v213."""
from pathlib import Path
source = Path(__file__).with_name("audit_press_shop_pr010_accepted_static_v210.py")
code = source.read_text(encoding="utf-8").replace("v210", "v213").replace("V210", "V213")
code = code.replace("PR008AuthoredAnchorCandidate_v213", "CumulativeReleaseCandidate_v213")
exec(compile(code, str(source) + "::v213", "exec"), globals(), globals())
