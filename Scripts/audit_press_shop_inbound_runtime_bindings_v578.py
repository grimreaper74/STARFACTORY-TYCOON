from pathlib import Path
code = Path(__file__).with_name("audit_press_shop_inbound_runtime_bindings_v574.py").read_text(encoding="utf-8")
code = code.replace("LB_PressShop_InboundIntegrationCandidate_v570", "LB_PressShop_InboundFunctionalCandidate_v577")
code = code.replace("inbound_runtime_bindings_v574.json", "inbound_runtime_bindings_v578.json")
code = code.replace("V574_COMPLETE", "V578_COMPLETE")
exec(compile(code, __file__ + "::v578", "exec"), globals(), globals())
