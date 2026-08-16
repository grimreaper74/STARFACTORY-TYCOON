"""Run the retained whole-shop PR010 navigation proof against exact v301."""
from pathlib import Path
source = Path(__file__).with_name("validate_press_shop_pr010_navigation_pie_v300.py")
code = source.read_text(encoding="utf-8")
code = code.replace(
    "/Game/LineBoss/Maps/LB_PressShop_TrainABalancedLightingCandidate_v300",
    "/Game/LineBoss/Maps/LB_PressShop_TrainAWideSpanClearanceCandidate_v301",
)
code = code.replace("press_shop_pr010_navigation_pie_v300", "press_shop_pr010_navigation_pie_v301")
code = code.replace("press-shop-pr010-navigation-pie-v300", "press-shop-pr010-navigation-pie-v301")
code = code.replace("PR010_V300", "PR010_V301")
exec(compile(code, str(source) + "::whole-shop-v301", "exec"), globals(), globals())
