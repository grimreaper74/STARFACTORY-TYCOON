"""Capture inherited v077 cameras on external-anchor-tabs candidate v082."""
from pathlib import Path

base = Path(__file__).with_name("capture_press_shop_pr008_native_runtime_v074.py")
code = base.read_text(encoding="utf-8")
code = code.replace("NativeRuntimeCandidate_v074", "ExternalAnchorTabsCandidate_v082")
code = code.replace("v074", "v082").replace("V074", "V082")
code = code.replace("LB_PR008_V082_CAM_NativeProcess", "LB_PR008_V077_CAM_CleanProcess")
code = code.replace("LB_PR008_V082_CAM_NativeMotion", "LB_PR008_V077_CAM_CleanMotion")
code = code.replace("LB_PR008_V082_CAM_NativeHMI", "LB_PR008_V077_CAM_CleanHMI")
code = code.replace("LB_PR008_V082_CAM_PR008ToPR009Interface", "LB_PR008_V077_CAM_ClearPR009Interface")
code = code.replace("press_shop_v082_pr008_native_process.png", "press_shop_v082_pr008_anchor_tabs_process.png")
code = code.replace("press_shop_v082_pr008_native_motion.png", "press_shop_v082_pr008_anchor_tabs_motion.png")
code = code.replace("press_shop_v082_pr008_native_hmi.png", "press_shop_v082_pr008_anchor_tabs_hmi.png")
exec(compile(code, str(base) + "::v082-external-anchor-adapter", "exec"), globals(), globals())
