"""v100 exact-map adapter for retained PR-010 runtime/collision/save authority proof."""

from pathlib import Path

base = Path(__file__).with_name("validate_press_shop_pr010_runtime_collision_pie_v099.py")
code = base.read_text(encoding="utf-8")
code = code.replace(
    "/Game/LineBoss/Maps/LB_PressShop_PR010CollisionNavigationCandidate_v099",
    "/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v100")
code = code.replace(
    "Saved/Audits/PR010_CollisionNavigation/runtime_collision_pie_audit_v099.json",
    "Saved/Audits/PR010_ReleaseArt_v100/runtime_collision_pie_audit_v100.json")
code = code.replace("pr010-runtime-collision-pie-v099", "pr010-release-art-runtime-collision-pie-v100")
code = code.replace("PR010_V099", "PR010_V100")
code = code.replace("V099", "V100")
exec(compile(code, str(base) + "::v100", "exec"), globals(), globals())
