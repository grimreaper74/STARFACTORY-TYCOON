"""Run inherited traceable PR004-to-PR005 handoff gate on cumulative v213."""
from pathlib import Path
source = Path(__file__).with_name("validate_press_shop_pr004_pr005_handoff_pie_v210.py")
code = source.read_text(encoding="utf-8").replace("v210", "v213").replace("V210", "V213")
code = code.replace("PR008AuthoredAnchorCandidate_v213", "CumulativeReleaseCandidate_v213")
exec(compile(code, str(source) + "::v213", "exec"), {"__name__": "__main__", "__file__": str(source)})
