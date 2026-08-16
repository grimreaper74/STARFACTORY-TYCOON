"""Run the proven collision/navigation audit against PR-008 Pro envelope v062."""
import os
from pathlib import Path

base = Path(__file__).with_name("audit_press_shop_pr004_collision_navigation_v026.py")
code = base.read_text(encoding="utf-8")
code = code.replace(
    '    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",',
    '    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",\n'
    '    "v062": "/Game/LineBoss/Maps/LB_PressShop_PR008ProEnvelopeCandidate_v062",')
code = code.replace('"v061")', '"v061", "v062")')
os.environ["LB_PR004_COLLISION_CANDIDATE"] = "v062"
exec(compile(code, str(base) + "::v062-adapter", "exec"), globals(), globals())
