from pathlib import Path
base=Path(__file__).with_name("validate_press_shop_expanded_whole_nav_pie_v368.py")
code=base.read_text(encoding="utf-8")
code=code.replace("/Game/LineBoss/Maps/LB_PressShop_ExpandedTrainNavOptimizedCandidate_v367","/Game/LineBoss/Developer/Validation/LB_PressShop_InboundNavConnectedCandidate_v586")
code=code.replace("press_shop_expanded_whole_nav_pie_v368.json","press_shop_inbound_whole_nav_pie_v592.json").replace("press-shop-expanded-whole-nav-pie-v368/v1","press-shop-inbound-whole-nav-pie-v592/v1")
exec(compile(code,str(base)+"::v592","exec"),globals(),globals())
