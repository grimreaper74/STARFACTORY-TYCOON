"""Run inherited static collision/navigation authority gates on v208."""

from pathlib import Path

source = Path(__file__).with_name("audit_press_shop_pr004_collision_navigation_v198.py")
code = source.read_text(encoding="utf-8").replace("v198", "v208").replace("V198", "V208")
code = code.replace("PR005AudioRuntimeCandidate_v208", "PR006ReleaseArtCandidate_v208")
exec(compile(code, str(source) + "::v208", "exec"), {"__name__": "__main__", "__file__": str(source)})
