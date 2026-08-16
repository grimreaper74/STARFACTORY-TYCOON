"""Run the inherited exact whole-shop management gate against v301."""
from pathlib import Path
source = Path(__file__).with_name("validate_press_shop_playable_management_pie_v300.py")
code = source.read_text(encoding="utf-8")
code = code.replace(
    "/Game/LineBoss/Maps/LB_PressShop_TrainABalancedLightingCandidate_v300",
    "/Game/LineBoss/Maps/LB_PressShop_TrainAWideSpanClearanceCandidate_v301",
)
code = code.replace("press_shop_playable_management_pie_v300", "press_shop_playable_management_pie_v301")
exec(compile(code, str(source) + "::exact-v301", "exec"), {"__name__": "__main__", "__file__": str(Path(__file__))})
