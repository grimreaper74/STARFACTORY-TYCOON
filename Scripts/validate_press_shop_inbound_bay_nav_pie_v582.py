from pathlib import Path
code=Path(__file__).with_name("validate_press_shop_inbound_bay_nav_pie_v580.py").read_text(encoding="utf-8")
code=code.replace("LB_PressShop_InboundFunctionalCandidate_v577","LB_PressShop_InboundNavCandidate_v581")
code=code.replace("inbound_bay_nav_pie_v580.json","inbound_bay_nav_pie_v582.json")
code=code.replace("v580/v1","v582/v1")
exec(compile(code,__file__+"::v582","exec"),globals(),globals())
