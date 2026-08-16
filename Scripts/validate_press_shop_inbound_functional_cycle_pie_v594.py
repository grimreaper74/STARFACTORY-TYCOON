from pathlib import Path
code=Path(__file__).with_name("validate_press_shop_inbound_functional_cycle_pie_v579.py").read_text(encoding="utf-8")
code=code.replace("LB_PressShop_InboundFunctionalCandidate_v577","LB_PressShop_InboundNavConnectedCandidate_v586")
code=code.replace("inbound_functional_cycle_pie_v579.json","inbound_functional_cycle_pie_v594.json").replace("v579/v1","v594/v1")
exec(compile(code,__file__+"::v594","exec"),globals(),globals())
