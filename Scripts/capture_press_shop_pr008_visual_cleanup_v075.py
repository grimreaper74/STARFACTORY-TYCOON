"""Adapt the v074 one-camera-per-process capture gate to visual-cleanup v075."""
import os
from pathlib import Path

import unreal

base = Path(__file__).with_name("capture_press_shop_pr008_native_runtime_v074.py")
code = base.read_text(encoding="utf-8")
code = code.replace("NativeRuntimeCandidate_v074", "VisualCleanupCandidate_v075")
code = code.replace("LB_PR008_V074_CAM_NativeProcess", "LB_PR008_V075_CAM_CleanProcess")
code = code.replace("LB_PR008_V074_CAM_NativeMotion", "LB_PR008_V075_CAM_CleanMotion")
code = code.replace("LB_PR008_V074_CAM_NativeHMI", "LB_PR008_V075_CAM_CleanHMI")
code = code.replace("LB_PR008_V074_CAM_PR008ToPR009Interface", "LB_PR008_V075_CAM_ClearPR009Interface")
code = code.replace("pr008_native_process", "pr008_clean_process")
code = code.replace("pr008_native_motion", "pr008_clean_motion")
code = code.replace("pr008_native_hmi", "pr008_clean_hmi")
code = code.replace("press_shop_v074_pr008_native_process.png", "press_shop_v075_pr008_clean_process.png")
code = code.replace("press_shop_v074_pr008_native_motion.png", "press_shop_v075_pr008_clean_motion.png")
code = code.replace("press_shop_v074_pr008_native_hmi.png", "press_shop_v075_pr008_clean_hmi.png")
code = code.replace("press_shop_v074_pr008_pr009_interface.png", "press_shop_v075_pr008_pr009_interface.png")
code = code.replace("v074", "v075").replace("V074", "V075")
os.environ["LB_PR005_CAPTURE_OUTPUT_DIR"] = str(
    Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/v075_pr005_runtime")
exec(compile(code, str(base) + "::v075-visual-cleanup-adapter", "exec"), globals(), globals())
