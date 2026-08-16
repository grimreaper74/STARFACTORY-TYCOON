"""Standing-player aisle/service regression on exact inbound candidate v570."""
from pathlib import Path
base = Path(__file__).with_name("validate_press_shop_expanded_aisle_collision_pie_v363.py")
code = base.read_text(encoding="utf-8")
code = code.replace("/Game/LineBoss/Maps/LB_PressShop_ExpandedTrainNavCandidate_v362", "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundIntegrationCandidate_v570")
code = code.replace("press_shop_expanded_aisle_collision_pie_v364.json", "press_shop_inbound_aisle_collision_pie_v573.json")
code = code.replace("press-shop-expanded-aisle-collision-pie-v364/v1", "press-shop-inbound-aisle-collision-pie-v573/v1")
exec(compile(code, str(base) + "::v573", "exec"), globals(), globals())
