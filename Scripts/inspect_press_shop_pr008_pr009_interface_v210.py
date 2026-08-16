"""Measure exact PR-008 to PR-009 interface on authored-anchor v210."""

from pathlib import Path

source = Path(__file__).with_name("inspect_press_shop_pr008_pr009_interface_v074.py")
code = source.read_text(encoding="utf-8")
code = code.replace("NativeRuntimeCandidate_v074", "AuthoredAnchorCandidate_v210")
code = code.replace("v074", "v210").replace("V074", "V210")
exec(compile(code, str(source) + "::v210-authored-anchor", "exec"), globals(), globals())
