"""Re-run exact PR-006 to Pro PR-008 joint bounds on v208."""

from pathlib import Path

source = Path(__file__).with_name("audit_press_shop_pr008_pro_entry_loop_continuity_v063.py")
code = source.read_text(encoding="utf-8")
code = code.replace(
    "/Game/LineBoss/Maps/LB_PressShop_PR008ProEntryLoopCandidate_v063",
    "/Game/LineBoss/Maps/LB_PressShop_PR006ReleaseArtCandidate_v208",
)
code = code.replace(
    "press_shop_pr008_pro_entry_loop_continuity_v063.json",
    "press_shop_pr008_pro_entry_loop_continuity_v208.json",
)
code = code.replace("press-shop-pr008-pro-entry-loop-continuity-v063", "press-shop-pr008-pro-entry-loop-continuity-v208")
code = code.replace("LINE_BOSS_PR008_V063_CONTINUITY", "LINE_BOSS_PR008_V208_CONTINUITY")
exec(compile(code, str(source) + "::v208", "exec"), globals(), globals())
