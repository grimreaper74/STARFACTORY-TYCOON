"""Use the direct v030 capture procedure against exact-map v031."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_cart_identity_v030.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainACartIdentityCandidate_v030", "LB_PressTrainACartLegibilityCandidate_v031")
code = code.replace("LB_PRESS_TRAIN_A_V030_CAPTURE", "LB_PRESS_TRAIN_A_V031_CAPTURE")
code = code.replace("press_train_a_v030", "press_train_a_v031")
code = code.replace("V030", "V031")
code = code.replace("v030", "v031")
exec(compile(code, str(base) + "::v031", "exec"), globals(), globals())
