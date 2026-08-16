"""Run the proven traceable-handoff gate against isolated PR-008 Pro envelope v062."""
import os
from pathlib import Path

base = Path(__file__).with_name("validate_press_shop_pr004_pr005_handoff_pie_v042.py")
code = base.read_text(encoding="utf-8")
code = code.replace(
    '    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",',
    '    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",\n'
    '    "v062": "/Game/LineBoss/Maps/LB_PressShop_PR008ProEnvelopeCandidate_v062",')
code = code.replace('"v061")', '"v061", "v062")')
os.environ["LB_PR004_PR005_HANDOFF_CANDIDATE"] = "v062"
exec(compile(code, str(base) + "::v062-adapter", "exec"), globals(), globals())
