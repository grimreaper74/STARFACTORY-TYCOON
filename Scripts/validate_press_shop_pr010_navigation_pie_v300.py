"""Run the retained whole-shop PR010 navigation proof against exact v300."""
from pathlib import Path
source = Path(__file__).with_name("validate_press_shop_pr010_navigation_pie_v295.py")
code = source.read_text(encoding="utf-8")
code = code.replace(
    "/Game/LineBoss/Maps/LB_PressShop_TrainAFabricatedShellOperatorFaceCandidate_v295",
    "/Game/LineBoss/Maps/LB_PressShop_TrainABalancedLightingCandidate_v300",
)
code = code.replace("press_shop_pr010_navigation_pie_v295", "press_shop_pr010_navigation_pie_v300")
code = code.replace("press-shop-pr010-navigation-pie-v295", "press-shop-pr010-navigation-pie-v300")
code = code.replace("PR010_V295", "PR010_V300")
exec(compile(code, str(source) + "::whole-shop-v300", "exec"), globals(), globals())
