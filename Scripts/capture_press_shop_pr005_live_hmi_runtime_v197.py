"""Exact-map inherited PR005 runtime/HMI capture wrapper for v197."""

from pathlib import Path


source = Path(__file__).with_name("capture_press_shop_pr005_live_hmi_runtime_v043.py")
code = source.read_text(encoding="utf-8")
needle = '    "v053": "/Game/LineBoss/Maps/LB_PressShop_PR005LogisticsCandidate_v053",'
code = code.replace(needle, needle + '\n    "v197": "/Game/LineBoss/Maps/LB_PressShop_PR005RuntimeCageInfillCandidate_v197",')
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
