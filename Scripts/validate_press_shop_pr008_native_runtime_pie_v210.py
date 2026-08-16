"""Run exact native PR-008 runtime gate on authored-anchor v210."""

from pathlib import Path

source = Path(__file__).with_name("validate_press_shop_pr008_native_runtime_pie_v074.py")
code = source.read_text(encoding="utf-8")
code = code.replace("NativeRuntimeCandidate_v074", "AuthoredAnchorCandidate_v210")
code = code.replace("v074", "v210").replace("V074", "V210")
# v074 predates the currently compiled save schema inherited by v107.
# Keep the stable-save check exact, but compare against today's authoritative
# PR-008 version 3 and Press Shop root format 10.
code = code.replace('"save_root_format": 7', '"save_root_format": 10')
code = code.replace('"station_save_version": 2', '"station_save_version": 3')
code = code.replace("stable.version != 2", "stable.version != 3")
exec(compile(code, str(source) + "::v210-authored-anchor", "exec"), globals(), globals())
