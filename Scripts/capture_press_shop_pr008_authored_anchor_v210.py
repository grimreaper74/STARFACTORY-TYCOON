"""Capture exact v210 authored-anchor PR-008 views."""

from pathlib import Path

source = Path(__file__).with_name("capture_press_shop_pr008_native_runtime_v074.py")
code = source.read_text(encoding="utf-8")
code = code.replace("v074", "v210").replace("V074", "V210")
code = code.replace("PR008NativeRuntimeCandidate_v210", "PR008AuthoredAnchorCandidate_v210")
code = code.replace("LB_PR008_V210_CAM_NativeProcess", "LB_PR008_V210_CAM_AuthoredAnchorProcess")
code = code.replace("LB_PR008_V210_CAM_NativeMotion", "LB_PR008_V210_CAM_AnchorOperatorClose")
code = code.replace("LB_PR008_V210_CAM_NativeHMI", "LB_PR008_V077_CAM_CleanHMI")
code = code.replace("LB_PR008_V210_CAM_PR008ToPR009Interface", "LB_PR008_V077_CAM_ClearPR009Interface")
code = code.replace("press_shop_v210_pr008_native_process.png", "press_shop_v210_pr008_authored_anchor_process.png")
code = code.replace("press_shop_v210_pr008_native_motion.png", "press_shop_v210_pr008_authored_anchor_close.png")
code = code.replace("press_shop_v210_pr008_native_hmi.png", "press_shop_v210_pr008_authored_anchor_hmi.png")
exec(compile(code, str(source) + "::v210-authored-anchor", "exec"), globals(), globals())
