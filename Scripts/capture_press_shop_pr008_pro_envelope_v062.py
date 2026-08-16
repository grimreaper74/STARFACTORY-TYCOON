"""Capture one PR-008 Pro-envelope fixed camera per Unreal process."""
import os
from pathlib import Path

base = Path(__file__).with_name("capture_press_shop_pr005_live_hmi_runtime_v043.py")
code = base.read_text(encoding="utf-8")
code = code.replace(
    '    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",',
    '    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",\n'
    '    "v062": "/Game/LineBoss/Maps/LB_PressShop_PR008ProEnvelopeCandidate_v062",')
code = code.replace(
    '    "pr006_runtime_connected": ("LB_PR008_V059_CAM_ConnectedLine", "press_shop_v061_pr006_runtime_connected.png"),',
    '    "pr006_runtime_connected": ("LB_PR008_V059_CAM_ConnectedLine", "press_shop_v061_pr006_runtime_connected.png"),\n'
    '    "pr008_pro_operator": ("LB_PR008_V062_CAM_Operator", "press_shop_v062_pr008_pro_operator.png"),\n'
    '    "pr008_pro_elevated": ("LB_PR008_V062_CAM_Elevated", "press_shop_v062_pr008_pro_elevated.png"),\n'
    '    "pr008_pro_connected": ("LB_PR008_V062_CAM_Connected", "press_shop_v062_pr008_pro_connected.png"),')
code = code.replace('"v061")', '"v061", "v062")')
code = code.replace('if CANDIDATE == "v061":', 'if CANDIDATE in ("v061", "v062"):')
os.environ["LB_PR005_CAPTURE_CANDIDATE"] = "v062"
exec(compile(code, str(base) + "::v062-adapter", "exec"), globals(), globals())
