"""Adapt the exact joint-bounds audit to the Pro entry-loop candidate v063."""
from pathlib import Path

base = Path(__file__).with_name("audit_press_shop_pr008_transition_continuity_v059.py")
code = base.read_text(encoding="utf-8")
replacements = (
    ("v059 PR-006-to-PR-008", "v063 PR-006-to-Pro-PR-008"),
    ("/Game/LineBoss/Maps/LB_PressShop_PR008TransitionGuardCandidate_v059", "/Game/LineBoss/Maps/LB_PressShop_PR008ProEntryLoopCandidate_v063"),
    ("press_shop_pr008_transition_continuity_v059.json", "press_shop_pr008_pro_entry_loop_continuity_v063.json"),
    ("LB_PR008_V059_PR008_TransitionStrip", "LB_PR008_V063_PR008_TransitionStrip"),
    ("LB_PR008_V058_PR008_ThreadedStrip", "LB_PR008_V062_11_StripCentreDatum"),
    ("press-shop-pr008-transition-continuity-v059", "press-shop-pr008-pro-entry-loop-continuity-v063"),
    ("LINE_BOSS_PR008_V059_CONTINUITY", "LINE_BOSS_PR008_V063_CONTINUITY"),
)
for old, new in replacements:
    code = code.replace(old, new)
exec(compile(code, str(base) + "::pro-entry-loop-v063", "exec"), globals(), globals())
