"""Capture inherited v077 fixed PR-008 cameras on calibrated-lighting v079."""
from pathlib import Path

base = Path(__file__).with_name("capture_press_shop_pr008_native_runtime_v074.py")
code = base.read_text(encoding="utf-8")
code = code.replace("NativeRuntimeCandidate_v074", "CalibratedLightingCandidate_v079")
code = code.replace("v074", "v079").replace("V074", "V079")
code = code.replace("LB_PR008_V079_CAM_NativeProcess", "LB_PR008_V077_CAM_CleanProcess")
code = code.replace("LB_PR008_V079_CAM_NativeMotion", "LB_PR008_V077_CAM_CleanMotion")
code = code.replace("LB_PR008_V079_CAM_NativeHMI", "LB_PR008_V077_CAM_CleanHMI")
code = code.replace("LB_PR008_V079_CAM_PR008ToPR009Interface", "LB_PR008_V077_CAM_ClearPR009Interface")
code = code.replace("press_shop_v079_pr008_native_process.png", "press_shop_v079_pr008_calibrated_process.png")
code = code.replace("press_shop_v079_pr008_native_motion.png", "press_shop_v079_pr008_calibrated_motion.png")
code = code.replace("press_shop_v079_pr008_native_hmi.png", "press_shop_v079_pr008_calibrated_hmi.png")
exec(compile(code, str(base) + "::v079-calibrated-adapter", "exec"), globals(), globals())
