from pathlib import Path
base=Path(__file__).with_name("validate_press_shop_inbound_functional_cycle_pie_v594.py")
code=base.read_text(encoding="utf-8").replace("LB_PressShop_InboundNavConnectedCandidate_v586","LB_PressShop_InboundReleaseCandidate_v597").replace("v594","v600").replace("V594","V600")
exec(compile(code,str(base)+"::v600","exec"),globals(),globals())
