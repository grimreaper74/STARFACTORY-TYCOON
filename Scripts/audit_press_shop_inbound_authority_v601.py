from pathlib import Path
base=Path(__file__).with_name("audit_press_shop_inbound_authority_v595.py")
code=base.read_text(encoding="utf-8").replace("LB_PressShop_InboundNavConnectedCandidate_v586","LB_PressShop_InboundReleaseCandidate_v597").replace("v595","v601").replace("V595","V601")
exec(compile(code,str(base)+"::v601","exec"),globals(),globals())
