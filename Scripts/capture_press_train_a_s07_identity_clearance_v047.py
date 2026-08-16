"""Use v046's five-camera capture procedure against exact-map v047."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_segmented_identity_v046.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainASegmentedIdentityCandidate_v046", "LB_PressTrainAS07IdentityClearanceCandidate_v047")
code = code.replace("LB_PRESS_TRAIN_A_V046_CAPTURE", "LB_PRESS_TRAIN_A_V047_CAPTURE")
code = code.replace("press_train_a_v046", "press_train_a_v047")
code = code.replace("V046", "V047").replace("v046", "v047")
exec(compile(code, str(base) + "::v047", "exec"), globals(), globals())
