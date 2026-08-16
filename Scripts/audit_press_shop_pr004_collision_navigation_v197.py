"""Exact-map collision/navigation wrapper for retained PR005 v197 candidate."""

from pathlib import Path


source = Path(__file__).with_name("audit_press_shop_pr004_collision_navigation_v026.py")
code = source.read_text(encoding="utf-8")
needle = '    "v053": "/Game/LineBoss/Maps/LB_PressShop_PR005LogisticsCandidate_v053",'
code = code.replace(needle, needle + '\n    "v197": "/Game/LineBoss/Maps/LB_PressShop_PR005RuntimeCageInfillCandidate_v197",')
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})

