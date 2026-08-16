"""Capture one detailed PR-008 Module 03 fixed camera per Unreal process."""
import os
from pathlib import Path
base = Path(__file__).with_name("capture_press_shop_pr005_live_hmi_runtime_v043.py")
code = base.read_text(encoding="utf-8")
code = code.replace('    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",', '    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",\n    "v066": "/Game/LineBoss/Maps/LB_PressShop_PR008Module03Candidate_v066",')
code = code.replace('    "pr006_runtime_connected": ("LB_PR008_V059_CAM_ConnectedLine", "press_shop_v061_pr006_runtime_connected.png"),', '    "pr006_runtime_connected": ("LB_PR008_V059_CAM_ConnectedLine", "press_shop_v061_pr006_runtime_connected.png"),\n    "pr008_module03_inspection": ("LB_PR008_V066_CAM_Module03Inspection", "press_shop_v066_pr008_module03_inspection.png"),\n    "pr008_module03_drive": ("LB_PR008_V066_CAM_Module03Drive", "press_shop_v066_pr008_module03_drive.png"),\n    "pr008_module03_elevated": ("LB_PR008_V066_CAM_Module03Elevated", "press_shop_v066_pr008_module03_elevated.png"),\n    "pr008_module03_connected": ("LB_PR008_V066_CAM_Module03Connected", "press_shop_v066_pr008_module03_connected.png"),')
code = code.replace('"v061")', '"v061", "v066")')
code = code.replace('if CANDIDATE == "v061":', 'if CANDIDATE in ("v061", "v066"):')
os.environ["LB_PR005_CAPTURE_CANDIDATE"] = "v066"
exec(compile(code, str(base) + "::v066-adapter", "exec"), globals(), globals())
