"""Capture one inherited fixed PR-008 camera per process on v078."""
from pathlib import Path

base = Path(__file__).with_name("capture_press_shop_pr008_native_runtime_v074.py")
code = base.read_text(encoding="utf-8")
code = code.replace("NativeRuntimeCandidate_v074", "ReflectionEnvironmentCandidate_v078")
code = code.replace("v074", "v078").replace("V074", "V078")
# v078 deliberately inherits the already accepted v077 camera transforms.
code = code.replace("LB_PR008_V078_CAM_NativeProcess", "LB_PR008_V077_CAM_CleanProcess")
code = code.replace("LB_PR008_V078_CAM_NativeMotion", "LB_PR008_V077_CAM_CleanMotion")
code = code.replace("LB_PR008_V078_CAM_NativeHMI", "LB_PR008_V077_CAM_CleanHMI")
code = code.replace("LB_PR008_V078_CAM_PR008ToPR009Interface", "LB_PR008_V077_CAM_ClearPR009Interface")
code = code.replace("press_shop_v078_pr008_native_process.png", "press_shop_v078_pr008_environment_process.png")
code = code.replace("press_shop_v078_pr008_native_motion.png", "press_shop_v078_pr008_environment_motion.png")
code = code.replace("press_shop_v078_pr008_native_hmi.png", "press_shop_v078_pr008_environment_hmi.png")
exec(compile(code, str(base) + "::v078-environment-adapter", "exec"), globals(), globals())
