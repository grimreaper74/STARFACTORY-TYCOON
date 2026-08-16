"""Run the inherited exact whole-shop management gate against v300."""
from pathlib import Path
source = Path(__file__).with_name("validate_press_shop_playable_management_pie_v295.py")
code = source.read_text(encoding="utf-8")
code = code.replace(
    "/Game/LineBoss/Maps/LB_PressShop_TrainAFabricatedShellOperatorFaceCandidate_v295",
    "/Game/LineBoss/Maps/LB_PressShop_TrainABalancedLightingCandidate_v300",
)
code = code.replace("press_shop_playable_management_pie_v295", "press_shop_playable_management_pie_v300")
exec(compile(code, str(source) + "::exact-v300", "exec"), {"__name__": "__main__", "__file__": str(Path(__file__))})
