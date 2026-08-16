"""Reuse v368 exact whole-shop navigation gate on fresh v374."""
from pathlib import Path
base=Path(__file__).with_name("validate_press_shop_expanded_whole_nav_pie_v368.py")
code=base.read_text(encoding="utf-8")
code=code.replace("LB_PressShop_ExpandedTrainNavOptimizedCandidate_v367","LB_PressShop_WideSpanTrussCandidate_v374")
code=code.replace("press_shop_expanded_whole_nav_pie_v368.json","press_shop_wide_span_whole_nav_pie_v376.json")
code=code.replace("expanded-whole-nav-pie-v368/v1","wide-span-whole-nav-pie-v376/v1")
exec(compile(code,str(base)+"::v376","exec"),globals(),globals())
