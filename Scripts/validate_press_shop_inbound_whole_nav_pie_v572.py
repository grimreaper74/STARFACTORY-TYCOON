"""Whole-shop navigation regression on exact inbound candidate v570."""
from pathlib import Path
base = Path(__file__).with_name("validate_press_shop_expanded_whole_nav_pie_v368.py")
code = base.read_text(encoding="utf-8")
code = code.replace("/Game/LineBoss/Maps/LB_PressShop_ExpandedTrainNavOptimizedCandidate_v367", "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundIntegrationCandidate_v570")
code = code.replace("press_shop_expanded_whole_nav_pie_v368.json", "press_shop_inbound_whole_nav_pie_v572.json")
code = code.replace("press-shop-expanded-whole-nav-pie-v368/v1", "press-shop-inbound-whole-nav-pie-v572/v1")
exec(compile(code, str(base) + "::v572", "exec"), globals(), globals())
