"""Adapt the v074 one-camera-per-process capture gate to layered-material v076."""
import os
from pathlib import Path

import unreal

base = Path(__file__).with_name("capture_press_shop_pr008_native_runtime_v074.py")
code = base.read_text(encoding="utf-8")
code = code.replace("NativeRuntimeCandidate_v074", "LayeredMaterialCandidate_v076")
code = code.replace("LB_PR008_V074_CAM_NativeProcess", "LB_PR008_V076_CAM_CleanProcess")
code = code.replace("LB_PR008_V074_CAM_NativeMotion", "LB_PR008_V076_CAM_CleanMotion")
code = code.replace("LB_PR008_V074_CAM_NativeHMI", "LB_PR008_V076_CAM_CleanHMI")
code = code.replace("LB_PR008_V074_CAM_PR008ToPR009Interface", "LB_PR008_V076_CAM_ClearPR009Interface")
code = code.replace("pr008_native_process", "pr008_layered_process")
code = code.replace("pr008_native_motion", "pr008_layered_motion")
code = code.replace("pr008_native_hmi", "pr008_layered_hmi")
code = code.replace("press_shop_v074_pr008_native_process.png", "press_shop_v076_pr008_layered_process.png")
code = code.replace("press_shop_v074_pr008_native_motion.png", "press_shop_v076_pr008_layered_motion.png")
code = code.replace("press_shop_v074_pr008_native_hmi.png", "press_shop_v076_pr008_layered_hmi.png")
code = code.replace("press_shop_v074_pr008_pr009_interface.png", "press_shop_v076_pr008_pr009_interface.png")
code = code.replace("v074", "v076").replace("V074", "V076")
os.environ["LB_PR005_CAPTURE_OUTPUT_DIR"] = str(
    Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/v076_pr005_runtime")
exec(compile(code, str(base) + "::v076-layered-material-adapter", "exec"), globals(), globals())
