"""Reuse v370 camera contract on fresh v374 structural successor."""
from pathlib import Path
base=Path(__file__).with_name("capture_press_shop_expanded_release_views_v370.py")
code=base.read_text(encoding="utf-8")
code=code.replace("LB_V370_VIEW","LB_V375_VIEW")
code=code.replace("v370_expanded_release_views","v375_wide_span_truss_views")
code=code.replace("LB_PressShop_ExpandedTrainNavOptimizedCandidate_v367","LB_PressShop_WideSpanTrussCandidate_v374")
code=code.replace("v367 load failed","v374 load failed")
code=code.replace("v370 task","v375 task")
code=code.replace("LB_V370_CAPTURE","LB_V375_CAPTURE")
exec(compile(code,str(base)+"::v375","exec"),globals(),globals())
