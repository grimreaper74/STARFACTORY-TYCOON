"""Capture one of five exact-map fixed Train A v033 views per process."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_cart_plate_clearance_v032.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainACartPlateClearanceCandidate_v032", "LB_PressTrainAEnclosedFacadeCandidate_v033")
code = code.replace("LB_PRESS_TRAIN_A_V032_CAPTURE", "LB_PRESS_TRAIN_A_V033_CAPTURE")
code = code.replace("press_train_a_v032", "press_train_a_v033")
code = code.replace("V032", "V033")
code = code.replace("v032", "v033")
exec(compile(code, str(base) + "::v033", "exec"), globals(), globals())
