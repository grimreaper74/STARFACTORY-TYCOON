"""v103 exact-map adapter for retained PR-010 support-route navigation proof."""

from pathlib import Path

base = Path(__file__).with_name("validate_press_shop_pr010_navigation_pie_v099.py")
code = base.read_text(encoding="utf-8")
code = code.replace("/Game/LineBoss/Maps/LB_PressShop_PR010CollisionNavigationCandidate_v099", "/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v103")
code = code.replace("Saved/Audits/PR010_CollisionNavigation/navigation_pie_audit_v099.json", "Saved/Audits/PR010_ReleaseArt_v103/navigation_pie_audit_v103.json")
code = code.replace("pr010-navigation-pie-v099", "pr010-release-art-navigation-pie-v103")
code = code.replace("PR010_V099", "PR010_V103")
exec(compile(code, str(base) + "::v103", "exec"), globals(), globals())
