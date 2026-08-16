"""Run inherited exact runtime navigation gate on v209."""

from pathlib import Path

source = Path(__file__).with_name("validate_press_shop_pr004_navigation_pie_v198.py")
code = source.read_text(encoding="utf-8").replace("v198", "v209").replace("V198", "V209")
code = code.replace("PR005AudioRuntimeCandidate_v209", "PR007ReleaseArtCandidate_v209")
exec(compile(code, str(source) + "::v209", "exec"), {"__name__": "__main__", "__file__": str(source)})
