"""Adapt the v074 one-camera-per-process capture gate to smooth-layer v077."""
import os
from pathlib import Path

import unreal

base = Path(__file__).with_name("capture_press_shop_pr008_native_runtime_v074.py")
code = base.read_text(encoding="utf-8")
code = code.replace("NativeRuntimeCandidate_v074", "SmoothLayerCandidate_v077")
code = code.replace("LB_PR008_V074_CAM_NativeProcess", "LB_PR008_V077_CAM_CleanProcess")
code = code.replace("LB_PR008_V074_CAM_NativeMotion", "LB_PR008_V077_CAM_CleanMotion")
code = code.replace("LB_PR008_V074_CAM_NativeHMI", "LB_PR008_V077_CAM_CleanHMI")
code = code.replace("LB_PR008_V074_CAM_PR008ToPR009Interface", "LB_PR008_V077_CAM_ClearPR009Interface")
code = code.replace("pr008_native_process", "pr008_smooth_process")
code = code.replace("pr008_native_motion", "pr008_smooth_motion")
code = code.replace("pr008_native_hmi", "pr008_smooth_hmi")
code = code.replace("press_shop_v074_pr008_native_process.png", "press_shop_v077_pr008_smooth_process.png")
code = code.replace("press_shop_v074_pr008_native_motion.png", "press_shop_v077_pr008_smooth_motion.png")
code = code.replace("press_shop_v074_pr008_native_hmi.png", "press_shop_v077_pr008_smooth_hmi.png")
code = code.replace("press_shop_v074_pr008_pr009_interface.png", "press_shop_v077_pr008_pr009_interface.png")
code = code.replace("v074", "v077").replace("V074", "V077")
os.environ["LB_PR005_CAPTURE_OUTPUT_DIR"] = str(
    Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/v077_pr005_runtime")
exec(compile(code, str(base) + "::v077-smooth-layer-adapter", "exec"), globals(), globals())
