from pathlib import Path
base=Path(__file__).with_name("validate_press_shop_inbound_whole_nav_pie_v592.py")
code=base.read_text(encoding="utf-8").replace("LB_PressShop_InboundNavConnectedCandidate_v586","LB_PressShop_InboundReleaseCandidate_v597").replace("v592","v598").replace("V592","V598")
exec(compile(code,str(base)+"::v598","exec"),globals(),globals())
