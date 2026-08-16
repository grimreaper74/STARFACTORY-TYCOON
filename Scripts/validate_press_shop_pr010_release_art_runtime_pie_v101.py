"""v101 exact-map adapter for retained PR-010 runtime/collision/save authority proof."""

from pathlib import Path

base = Path(__file__).with_name("validate_press_shop_pr010_runtime_collision_pie_v099.py")
code = base.read_text(encoding="utf-8")
code = code.replace("/Game/LineBoss/Maps/LB_PressShop_PR010CollisionNavigationCandidate_v099", "/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v101")
code = code.replace("Saved/Audits/PR010_CollisionNavigation/runtime_collision_pie_audit_v099.json", "Saved/Audits/PR010_ReleaseArt_v101/runtime_collision_pie_audit_v101.json")
code = code.replace("pr010-runtime-collision-pie-v099", "pr010-release-art-runtime-collision-pie-v101")
code = code.replace("PR010_V099", "PR010_V101").replace("V099", "V101")
exec(compile(code, str(base) + "::v101", "exec"), globals(), globals())
