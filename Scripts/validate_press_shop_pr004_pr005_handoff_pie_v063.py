"""Run the traceable-handoff gate against PR-008 Pro entry-loop v063."""
import os
from pathlib import Path
base = Path(__file__).with_name("validate_press_shop_pr004_pr005_handoff_pie_v042.py")
code = base.read_text(encoding="utf-8")
code = code.replace('    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",', '    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",\n    "v063": "/Game/LineBoss/Maps/LB_PressShop_PR008ProEntryLoopCandidate_v063",')
code = code.replace('"v061")', '"v061", "v063")')
os.environ["LB_PR004_PR005_HANDOFF_CANDIDATE"] = "v063"
exec(compile(code, str(base) + "::v063-adapter", "exec"), globals(), globals())
