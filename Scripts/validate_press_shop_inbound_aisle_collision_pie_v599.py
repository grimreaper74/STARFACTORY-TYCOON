from pathlib import Path
base=Path(__file__).with_name("validate_press_shop_inbound_aisle_collision_pie_v593.py")
code=base.read_text(encoding="utf-8").replace("LB_PressShop_InboundNavConnectedCandidate_v586","LB_PressShop_InboundReleaseCandidate_v597").replace("v593","v599").replace("V593","V599")
exec(compile(code,str(base)+"::v599","exec"),globals(),globals())
