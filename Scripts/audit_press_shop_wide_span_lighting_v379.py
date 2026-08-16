"""Reuse exact lighting/exposure inventory on v374."""
from pathlib import Path
base=Path(__file__).with_name("audit_press_shop_train_a_lighting_v295.py")
code=base.read_text(encoding="utf-8")
code=code.replace("LB_PressShop_TrainAFabricatedShellOperatorFaceCandidate_v295","LB_PressShop_WideSpanTrussCandidate_v374")
code=code.replace("press_shop_train_a_lighting_exposure_audit_v295.json","press_shop_wide_span_lighting_exposure_audit_v379.json")
code=code.replace("5CF8715BEE1F55EF98E1B9B713C74BF4F9C87281FE209FA190D73DA61DE94ABF","DDB934BEB76EE377E5E19B36D24C92888AEDC08946774EDC2998FEC58CA06F81")
code=code.replace("v295 hash drift","v374 hash drift")
code=code.replace("read-only audit changed v295","read-only audit changed v374")
code=code.replace("train-a-lighting-exposure-v295/v1","wide-span-lighting-exposure-v379/v1")
code=code.replace("EXACT_V295","EXACT_V374")
exec(compile(code,str(base)+"::v379","exec"),globals(),globals())
