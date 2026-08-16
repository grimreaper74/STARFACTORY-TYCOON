"""Capture one detailed PR-008 Module 09 fixed camera per Unreal process."""
import os
from pathlib import Path

base = Path(__file__).with_name("capture_press_shop_pr005_live_hmi_runtime_v043.py")
code = base.read_text(encoding="utf-8")
code = code.replace(
    '    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",',
    '    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",\n'
    '    "v072": "/Game/LineBoss/Maps/LB_PressShop_PR008Module09Candidate_v072",')
code = code.replace(
    '    "pr006_runtime_connected": ("LB_PR008_V059_CAM_ConnectedLine", "press_shop_v061_pr006_runtime_connected.png"),',
    '    "pr006_runtime_connected": ("LB_PR008_V059_CAM_ConnectedLine", "press_shop_v061_pr006_runtime_connected.png"),\n'
    '    "pr008_module09_inspection": ("LB_PR008_V072_CAM_Module09Inspection", "press_shop_v072_pr008_module09_inspection.png"),\n'
    '    "pr008_module09_rear_service": ("LB_PR008_V072_CAM_Module09RearService", "press_shop_v072_pr008_module09_rear_service.png"),\n'
    '    "pr008_module09_elevated": ("LB_PR008_V072_CAM_Module09Elevated", "press_shop_v072_pr008_module09_elevated.png"),\n'
    '    "pr008_module09_connected": ("LB_PR008_V072_CAM_Module09Connected", "press_shop_v072_pr008_module09_connected.png"),')
code = code.replace('"v061")', '"v061", "v072")')
code = code.replace('if CANDIDATE == "v061":', 'if CANDIDATE in ("v061", "v072"):')
os.environ["LB_PR005_CAPTURE_CANDIDATE"] = "v072"
exec(compile(code, str(base) + "::v072-module09-adapter", "exec"), globals(), globals())
