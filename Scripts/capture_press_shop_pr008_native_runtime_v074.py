"""Capture one fixed v074 native PR-008 camera per Unreal process."""
import os
from pathlib import Path

base = Path(__file__).with_name("capture_press_shop_pr005_live_hmi_runtime_v043.py")
code = base.read_text(encoding="utf-8")
code = code.replace(
    '    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",',
    '    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",\n'
    '    "v074": "/Game/LineBoss/Maps/LB_PressShop_PR008NativeRuntimeCandidate_v074",')
code = code.replace(
    '    "pr006_runtime_connected": ("LB_PR008_V059_CAM_ConnectedLine", "press_shop_v061_pr006_runtime_connected.png"),',
    '    "pr006_runtime_connected": ("LB_PR008_V059_CAM_ConnectedLine", "press_shop_v061_pr006_runtime_connected.png"),\n'
    '    "pr008_native_process": ("LB_PR008_V074_CAM_NativeProcess", "press_shop_v074_pr008_native_process.png"),\n'
    '    "pr008_native_motion": ("LB_PR008_V074_CAM_NativeMotion", "press_shop_v074_pr008_native_motion.png"),\n'
    '    "pr008_native_hmi": ("LB_PR008_V074_CAM_NativeHMI", "press_shop_v074_pr008_native_hmi.png"),\n'
    '    "pr008_pr009_interface": ("LB_PR008_V074_CAM_PR008ToPR009Interface", "press_shop_v074_pr008_pr009_interface.png"),')
code = code.replace('"v061")', '"v061", "v074")')
code = code.replace('if CANDIDATE == "v061":', 'if CANDIDATE == "v061":')
os.environ["LB_PR005_CAPTURE_CANDIDATE"] = "v074"
exec(compile(code, str(base) + "::v074-pr008-native-adapter", "exec"), globals(), globals())
