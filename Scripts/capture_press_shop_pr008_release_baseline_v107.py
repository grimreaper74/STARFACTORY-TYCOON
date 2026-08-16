"""Capture retained PR-008 fixed cameras on the exact full-line v107 parent."""

from pathlib import Path

source = Path(__file__).with_name("capture_press_shop_pr008_native_runtime_v074.py")
code = source.read_text(encoding="utf-8")
code = code.replace("v074", "v107").replace("V074", "V107")
code = code.replace("PR008NativeRuntimeCandidate_v107", "IntegratedEnvironmentCandidate_v107")
code = code.replace("LB_PR008_V107_CAM_NativeProcess", "LB_PR008_V077_CAM_CleanProcess")
code = code.replace("LB_PR008_V107_CAM_NativeMotion", "LB_PR008_V077_CAM_CleanMotion")
code = code.replace("LB_PR008_V107_CAM_NativeHMI", "LB_PR008_V077_CAM_CleanHMI")
code = code.replace("LB_PR008_V107_CAM_PR008ToPR009Interface", "LB_PR008_V077_CAM_ClearPR009Interface")
code = code.replace("press_shop_v107_pr008_native_process.png", "press_shop_v107_pr008_release_baseline_process.png")
code = code.replace("press_shop_v107_pr008_native_motion.png", "press_shop_v107_pr008_release_baseline_motion.png")
code = code.replace("press_shop_v107_pr008_native_hmi.png", "press_shop_v107_pr008_release_baseline_hmi.png")
exec(compile(code, str(source) + "::v107-release-baseline", "exec"), globals(), globals())
