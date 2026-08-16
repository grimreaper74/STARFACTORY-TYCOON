"""Run an inherited v288 gate against exact v301."""
from pathlib import Path
source = Path(__file__).with_name("run_exact_press_shop_v300_gate.py")
code = source.read_text(encoding="utf-8")
code = code.replace("LB_V300_GATE", "LB_V301_GATE")
code = code.replace(
    "/Game/LineBoss/Maps/LB_PressShop_TrainABalancedLightingCandidate_v300",
    "/Game/LineBoss/Maps/LB_PressShop_TrainAWideSpanClearanceCandidate_v301",
)
code = code.replace("v300", "v301").replace("V300", "V301")
exec(compile(code, str(source) + "::exact-v301", "exec"), {"__name__": "__main__", "__file__": str(Path(__file__))})
