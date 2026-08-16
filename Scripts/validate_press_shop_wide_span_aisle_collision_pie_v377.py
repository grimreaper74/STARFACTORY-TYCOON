"""Reuse v364 collision/service-envelope gate on fresh v374."""
from pathlib import Path
base=Path(__file__).with_name("validate_press_shop_expanded_aisle_collision_pie_v363.py")
code=base.read_text(encoding="utf-8")
code=code.replace("LB_PressShop_ExpandedTrainNavCandidate_v362","LB_PressShop_WideSpanTrussCandidate_v374")
code=code.replace("press_shop_expanded_aisle_collision_pie_v364.json","press_shop_wide_span_aisle_collision_pie_v377.json")
code=code.replace("expanded-aisle-collision-pie-v364/v1","wide-span-aisle-collision-pie-v377/v1")
exec(compile(code,str(base)+"::v377","exec"),globals(),globals())
