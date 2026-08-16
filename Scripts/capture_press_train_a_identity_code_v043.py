"""Use v041's five-camera capture procedure against exact-map v043."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_physical_identity_v041.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAPhysicalIdentityCandidate_v041", "LB_PressTrainAIdentityCodeCandidate_v043")
code = code.replace("LB_PRESS_TRAIN_A_V041_CAPTURE", "LB_PRESS_TRAIN_A_V043_CAPTURE")
code = code.replace("press_train_a_v041", "press_train_a_v043")
code = code.replace("V041", "V043").replace("v041", "v043")
exec(compile(code, str(base) + "::v043", "exec"), globals(), globals())
