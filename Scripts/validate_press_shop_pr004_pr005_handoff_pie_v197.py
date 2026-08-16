"""Exact-map PR004-to-PR005 handoff wrapper for retained v197 candidate."""

from pathlib import Path


source = Path(__file__).with_name("validate_press_shop_pr004_pr005_handoff_pie_v042.py")
code = source.read_text(encoding="utf-8")
needle = '    "v053": "/Game/LineBoss/Maps/LB_PressShop_PR005LogisticsCandidate_v053",'
code = code.replace(needle, needle + '\n    "v197": "/Game/LineBoss/Maps/LB_PressShop_PR005RuntimeCageInfillCandidate_v197",')
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})

