"""Run inherited static collision/navigation authority gates on v210."""

from pathlib import Path

source = Path(__file__).with_name("audit_press_shop_pr004_collision_navigation_v198.py")
code = source.read_text(encoding="utf-8").replace("v198", "v210").replace("V198", "V210")
code = code.replace("PR005AudioRuntimeCandidate_v210", "PR008AuthoredAnchorCandidate_v210")
exec(compile(code, str(source) + "::v210", "exec"), {"__name__": "__main__", "__file__": str(source)})
