"""Use the direct v031 capture procedure against exact-map v032."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_cart_legibility_v031.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainACartLegibilityCandidate_v031", "LB_PressTrainACartPlateClearanceCandidate_v032")
code = code.replace("LB_PRESS_TRAIN_A_V031_CAPTURE", "LB_PRESS_TRAIN_A_V032_CAPTURE")
code = code.replace("press_train_a_v031", "press_train_a_v032")
code = code.replace("V031", "V032")
code = code.replace("v031", "v032")
exec(compile(code, str(base) + "::v032", "exec"), globals(), globals())
