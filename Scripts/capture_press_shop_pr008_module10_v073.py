"""Capture one detailed PR-008 Module 10 fixed camera per Unreal process."""
import os
from pathlib import Path

base = Path(__file__).with_name("capture_press_shop_pr005_live_hmi_runtime_v043.py")
code = base.read_text(encoding="utf-8")
code = code.replace(
    '    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",',
    '    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",\n'
    '    "v073": "/Game/LineBoss/Maps/LB_PressShop_PR008Module10Candidate_v073",')
code = code.replace(
    '    "pr006_runtime_connected": ("LB_PR008_V059_CAM_ConnectedLine", "press_shop_v061_pr006_runtime_connected.png"),',
    '    "pr006_runtime_connected": ("LB_PR008_V059_CAM_ConnectedLine", "press_shop_v061_pr006_runtime_connected.png"),\n'
    '    "pr008_module10_operator": ("LB_PR008_V073_CAM_Module10Operator", "press_shop_v073_pr008_module10_operator.png"),\n'
    '    "pr008_module10_inspection": ("LB_PR008_V073_CAM_Module10Inspection", "press_shop_v073_pr008_module10_inspection.png"),\n'
    '    "pr008_module10_elevated": ("LB_PR008_V073_CAM_Module10Elevated", "press_shop_v073_pr008_module10_elevated.png"),\n'
    '    "pr008_module10_connected": ("LB_PR008_V073_CAM_Module10Connected", "press_shop_v073_pr008_module10_connected.png"),')
code = code.replace('"v061")', '"v061", "v073")')
code = code.replace('if CANDIDATE == "v061":', 'if CANDIDATE in ("v061", "v073"):')
os.environ["LB_PR005_CAPTURE_CANDIDATE"] = "v073"
exec(compile(code, str(base) + "::v073-module10-adapter", "exec"), globals(), globals())
