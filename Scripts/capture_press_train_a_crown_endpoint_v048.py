"""Use v047's five-camera capture procedure against exact-map v048."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_s07_identity_clearance_v047.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAS07IdentityClearanceCandidate_v047", "LB_PressTrainACrownEndpointCandidate_v048")
code = code.replace("LB_PRESS_TRAIN_A_V047_CAPTURE", "LB_PRESS_TRAIN_A_V048_CAPTURE")
code = code.replace("press_train_a_v047", "press_train_a_v048")
code = code.replace("V047", "V048").replace("v047", "v048")
exec(compile(code, str(base) + "::v048", "exec"), globals(), globals())
