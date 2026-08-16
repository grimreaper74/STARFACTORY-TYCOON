"""Capture one detailed PR-008 Module 05 fixed camera per Unreal process."""
import os
from pathlib import Path
base = Path(__file__).with_name("capture_press_shop_pr005_live_hmi_runtime_v043.py")
code = base.read_text(encoding="utf-8")
code = code.replace('    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",', '    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",\n    "v068": "/Game/LineBoss/Maps/LB_PressShop_PR008Module05Candidate_v068",')
code = code.replace('    "pr006_runtime_connected": ("LB_PR008_V059_CAM_ConnectedLine", "press_shop_v061_pr006_runtime_connected.png"),', '    "pr006_runtime_connected": ("LB_PR008_V059_CAM_ConnectedLine", "press_shop_v061_pr006_runtime_connected.png"),\n    "pr008_module05_inspection": ("LB_PR008_V068_CAM_Module05Inspection", "press_shop_v068_pr008_module05_inspection.png"),\n    "pr008_module05_drive": ("LB_PR008_V068_CAM_Module05Drive", "press_shop_v068_pr008_module05_drive.png"),\n    "pr008_module05_elevated": ("LB_PR008_V068_CAM_Module05Elevated", "press_shop_v068_pr008_module05_elevated.png"),\n    "pr008_module05_connected": ("LB_PR008_V068_CAM_Module05Connected", "press_shop_v068_pr008_module05_connected.png"),')
code = code.replace('"v061")', '"v061", "v068")')
code = code.replace('if CANDIDATE == "v061":', 'if CANDIDATE in ("v061", "v068"):')
os.environ["LB_PR005_CAPTURE_CANDIDATE"] = "v068"
exec(compile(code, str(base) + "::v068-adapter", "exec"), globals(), globals())
