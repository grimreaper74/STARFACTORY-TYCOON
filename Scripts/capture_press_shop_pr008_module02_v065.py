"""Capture one detailed PR-008 Module 02 fixed camera per Unreal process."""
import os
from pathlib import Path
base = Path(__file__).with_name("capture_press_shop_pr005_live_hmi_runtime_v043.py")
code = base.read_text(encoding="utf-8")
code = code.replace('    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",', '    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",\n    "v065": "/Game/LineBoss/Maps/LB_PressShop_PR008Module02Candidate_v065",')
code = code.replace('    "pr006_runtime_connected": ("LB_PR008_V059_CAM_ConnectedLine", "press_shop_v061_pr006_runtime_connected.png"),', '    "pr006_runtime_connected": ("LB_PR008_V059_CAM_ConnectedLine", "press_shop_v061_pr006_runtime_connected.png"),\n    "pr008_module02_inspection": ("LB_PR008_V065_CAM_Module02Inspection", "press_shop_v065_pr008_module02_inspection.png"),\n    "pr008_module02_drive": ("LB_PR008_V065_CAM_Module02Drive", "press_shop_v065_pr008_module02_drive.png"),\n    "pr008_module02_elevated": ("LB_PR008_V065_CAM_Module02Elevated", "press_shop_v065_pr008_module02_elevated.png"),\n    "pr008_module02_connected": ("LB_PR008_V065_CAM_Module02Connected", "press_shop_v065_pr008_module02_connected.png"),')
code = code.replace('"v061")', '"v061", "v065")')
code = code.replace('if CANDIDATE == "v061":', 'if CANDIDATE in ("v061", "v065"):')
os.environ["LB_PR005_CAPTURE_CANDIDATE"] = "v065"
exec(compile(code, str(base) + "::v065-adapter", "exec"), globals(), globals())
