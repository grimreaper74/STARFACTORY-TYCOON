"""Capture one fixed PR-009 v083 validation camera per Unreal process."""
import os
from pathlib import Path

base = Path(__file__).with_name("capture_press_shop_pr005_live_hmi_runtime_v043.py")
code = base.read_text(encoding="utf-8")
code = code.replace(
    '    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",',
    '    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",\n'
    '    "v083": "/Game/LineBoss/Maps/LB_PressShop_PR009PhysicalIntegrationCandidate_v083",')
code = code.replace(
    '    "pr006_runtime_connected": ("LB_PR008_V059_CAM_ConnectedLine", "press_shop_v061_pr006_runtime_connected.png"),',
    '    "pr006_runtime_connected": ("LB_PR008_V059_CAM_ConnectedLine", "press_shop_v061_pr006_runtime_connected.png"),\n'
    '    "pr009_process": ("LB_PR009_V083_CAM_Process", "press_shop_v083_pr009_process.png"),\n'
    '    "pr009_interface": ("LB_PR009_V083_CAM_Interface", "press_shop_v083_pr009_interface.png"),\n'
    '    "pr009_cell": ("LB_PR009_V083_CAM_PR009Cell", "press_shop_v083_pr009_cell.png"),\n'
    '    "pr009_elevated": ("LB_PR009_V083_CAM_Elevated", "press_shop_v083_pr009_elevated.png"),')
os.environ["LB_PR005_CAPTURE_CANDIDATE"] = "v083"
exec(compile(code, str(base) + "::v083-pr009-physical-adapter", "exec"), globals(), globals())
