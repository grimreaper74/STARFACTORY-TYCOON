"""Capture one detailed PR-008 Module 04 fixed camera per Unreal process."""
import os
from pathlib import Path
base = Path(__file__).with_name("capture_press_shop_pr005_live_hmi_runtime_v043.py")
code = base.read_text(encoding="utf-8")
code = code.replace('    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",', '    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",\n    "v067": "/Game/LineBoss/Maps/LB_PressShop_PR008Module04Candidate_v067",')
code = code.replace('    "pr006_runtime_connected": ("LB_PR008_V059_CAM_ConnectedLine", "press_shop_v061_pr006_runtime_connected.png"),', '    "pr006_runtime_connected": ("LB_PR008_V059_CAM_ConnectedLine", "press_shop_v061_pr006_runtime_connected.png"),\n    "pr008_module04_inspection": ("LB_PR008_V067_CAM_Module04Inspection", "press_shop_v067_pr008_module04_inspection.png"),\n    "pr008_module04_drive": ("LB_PR008_V067_CAM_Module04Drive", "press_shop_v067_pr008_module04_drive.png"),\n    "pr008_module04_elevated": ("LB_PR008_V067_CAM_Module04Elevated", "press_shop_v067_pr008_module04_elevated.png"),\n    "pr008_module04_connected": ("LB_PR008_V067_CAM_Module04Connected", "press_shop_v067_pr008_module04_connected.png"),')
code = code.replace('"v061")', '"v061", "v067")')
code = code.replace('if CANDIDATE == "v061":', 'if CANDIDATE in ("v061", "v067"):')
os.environ["LB_PR005_CAPTURE_CANDIDATE"] = "v067"
exec(compile(code, str(base) + "::v067-adapter", "exec"), globals(), globals())
