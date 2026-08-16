"""Capture one inherited fixed-camera view of isolated modular Train A v302."""
from pathlib import Path
base=Path(__file__).with_name("capture_press_shop_train_a_wide_span_clearance_v301.py")
code=base.read_text(encoding="utf-8")
code=code.replace("LB_PressShop_TrainAWideSpanClearanceCandidate_v301","LB_PressShop_TrainAModularVisualIntakeCandidate_v302")
code=code.replace("LB_V301_CAPTURE","LB_V302_CAPTURE")
code=code.replace("v301_train_a_operator.png","v302_train_a_operator.png").replace("v301_train_a_flow.png","v302_train_a_flow.png").replace("v301_four_train_overview.png","v302_four_train_overview.png")
code=code.replace("v301_train_a_wide_span_clearance","v302_train_a_modular_visual")
code=code.replace("Cairnwell v301 wide-span","Cairnwell v302 modular Train A")
code=code.replace("LB_V301_CAPTURE_PASS","LB_V302_CAPTURE_PASS").replace("LB_V301_CAPTURE_FAIL","LB_V302_CAPTURE_FAIL")
exec(compile(code,str(base)+"::v302","exec"),globals(),globals())
