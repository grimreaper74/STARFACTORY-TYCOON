from pathlib import Path
code=Path(__file__).with_name("audit_press_shop_inbound_authority_v571.py").read_text(encoding="utf-8")
code=code.replace("LB_PressShop_InboundIntegrationCandidate_v570","LB_PressShop_InboundNavConnectedCandidate_v586")
code=code.replace("LB_PressShop_InboundIntegrationCandidate_v570.umap","LB_PressShop_InboundNavConnectedCandidate_v586.umap")
code=code.replace("inbound_exact_authority_v571.json","inbound_exact_authority_v595.json")
code=code.replace('"thirteen_inbound_modules": len(modules) == 13,','"thirteen_inbound_modules": len(modules) == 13,\n    "one_inbound_delivery_controller": controllers.get("LBInboundDeliveryController",0) == 1,')
code=code.replace("LINE_BOSS_INBOUND_EXACT_AUTHORITY_V571_PASS","LINE_BOSS_INBOUND_EXACT_AUTHORITY_V595_PASS")
exec(compile(code,__file__+"::v595","exec"),globals(),globals())
