"""Run the retained whole-shop PR010 navigation proof against exact v295."""

from pathlib import Path


base = Path(__file__).with_name("validate_press_shop_pr010_navigation_pie_v099.py")
code = base.read_text(encoding="utf-8")
code = code.replace(
    "/Game/LineBoss/Maps/LB_PressShop_PR010CollisionNavigationCandidate_v099",
    "/Game/LineBoss/Maps/LB_PressShop_TrainAFabricatedShellOperatorFaceCandidate_v295",
)
code = code.replace(
    "Saved/Audits/PR010_CollisionNavigation/navigation_pie_audit_v099.json",
    "Saved/Audits/PressShopIntegration/press_shop_pr010_navigation_pie_v295.json",
)
code = code.replace("pr010-navigation-pie-v099", "press-shop-pr010-navigation-pie-v295")
code = code.replace("PR010_V099", "PR010_V295")
exec(compile(code, str(base) + "::whole-shop-v295", "exec"), globals(), globals())
