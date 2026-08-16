"""Run an inherited v288 dock/PR009 gate against exact v300."""
import os
from pathlib import Path
source = Path(__file__).with_name("run_exact_press_shop_v295_gate.py")
code = source.read_text(encoding="utf-8")
code = code.replace("LB_V295_GATE", "LB_V300_GATE")
code = code.replace(
    "/Game/LineBoss/Maps/LB_PressShop_TrainAFabricatedShellOperatorFaceCandidate_v295",
    "/Game/LineBoss/Maps/LB_PressShop_TrainABalancedLightingCandidate_v300",
)
code = code.replace("v295", "v300").replace("V295", "V300")
exec(compile(code, str(source) + "::exact-v300", "exec"), {"__name__": "__main__", "__file__": str(Path(__file__))})
