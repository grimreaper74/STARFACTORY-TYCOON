"""Use the direct v029 capture procedure against exact-map v030."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_cart_mechanical_evidence_v029.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainACartMechanicalEvidenceCandidate_v029", "LB_PressTrainACartIdentityCandidate_v030")
code = code.replace("LB_PRESS_TRAIN_A_V029_CAPTURE", "LB_PRESS_TRAIN_A_V030_CAPTURE")
code = code.replace("press_train_a_v029", "press_train_a_v030")
code = code.replace("V029", "V030")
code = code.replace("v029", "v030")
exec(compile(code, str(base) + "::v030", "exec"), globals(), globals())
