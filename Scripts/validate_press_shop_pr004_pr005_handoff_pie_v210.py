"""Run inherited traceable PR-004 to PR-005 handoff gate on v210."""

from pathlib import Path

source = Path(__file__).with_name("validate_press_shop_pr004_pr005_handoff_pie_v198.py")
code = source.read_text(encoding="utf-8").replace("v198", "v210").replace("V198", "V210")
code = code.replace("PR005AudioRuntimeCandidate_v210", "PR008AuthoredAnchorCandidate_v210")
exec(compile(code, str(source) + "::v210", "exec"), {"__name__": "__main__", "__file__": str(source)})
