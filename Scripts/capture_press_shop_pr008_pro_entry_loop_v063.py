"""Capture one guarded Pro entry-loop fixed camera per Unreal process."""
import os
from pathlib import Path
base = Path(__file__).with_name("capture_press_shop_pr005_live_hmi_runtime_v043.py")
code = base.read_text(encoding="utf-8")
code = code.replace('    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",', '    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",\n    "v063": "/Game/LineBoss/Maps/LB_PressShop_PR008ProEntryLoopCandidate_v063",')
code = code.replace('    "pr006_runtime_connected": ("LB_PR008_V059_CAM_ConnectedLine", "press_shop_v061_pr006_runtime_connected.png"),', '    "pr006_runtime_connected": ("LB_PR008_V059_CAM_ConnectedLine", "press_shop_v061_pr006_runtime_connected.png"),\n    "pr008_pro_transition_operator": ("LB_PR008_V063_CAM_TransitionOperator", "press_shop_v063_pr008_pro_transition_operator.png"),\n    "pr008_pro_transition_elevated": ("LB_PR008_V063_CAM_TransitionElevated", "press_shop_v063_pr008_pro_transition_elevated.png"),\n    "pr008_pro_transition_connected": ("LB_PR008_V063_CAM_ConnectedLine", "press_shop_v063_pr008_pro_transition_connected.png"),')
code = code.replace('"v061")', '"v061", "v063")')
code = code.replace('if CANDIDATE == "v061":', 'if CANDIDATE in ("v061", "v063"):')
os.environ["LB_PR005_CAPTURE_CANDIDATE"] = "v063"
exec(compile(code, str(base) + "::v063-adapter", "exec"), globals(), globals())
