"""Capture one detailed PR-008 Module 01 fixed camera per Unreal process."""
import os
from pathlib import Path
base = Path(__file__).with_name("capture_press_shop_pr005_live_hmi_runtime_v043.py")
code = base.read_text(encoding="utf-8")
code = code.replace('    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",', '    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",\n    "v064": "/Game/LineBoss/Maps/LB_PressShop_PR008Module01Candidate_v064",')
code = code.replace('    "pr006_runtime_connected": ("LB_PR008_V059_CAM_ConnectedLine", "press_shop_v061_pr006_runtime_connected.png"),', '    "pr006_runtime_connected": ("LB_PR008_V059_CAM_ConnectedLine", "press_shop_v061_pr006_runtime_connected.png"),\n    "pr008_module01_operator": ("LB_PR008_V064_CAM_Module01Operator", "press_shop_v064_pr008_module01_operator.png"),\n    "pr008_module01_inspection": ("LB_PR008_V064_CAM_Module01Inspection", "press_shop_v064_pr008_module01_inspection.png"),\n    "pr008_module01_elevated": ("LB_PR008_V064_CAM_Module01Elevated", "press_shop_v064_pr008_module01_elevated.png"),\n    "pr008_module01_connected": ("LB_PR008_V064_CAM_Module01Connected", "press_shop_v064_pr008_module01_connected.png"),')
code = code.replace('"v061")', '"v061", "v064")')
code = code.replace('if CANDIDATE == "v061":', 'if CANDIDATE in ("v061", "v064"):')
os.environ["LB_PR005_CAPTURE_CANDIDATE"] = "v064"
exec(compile(code, str(base) + "::v064-adapter", "exec"), globals(), globals())
