"""Use v044's five-camera capture procedure against exact-map v046."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_raised_identity_v044.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainARaisedIdentityCandidate_v044", "LB_PressTrainASegmentedIdentityCandidate_v046")
code = code.replace("LB_PRESS_TRAIN_A_V044_CAPTURE", "LB_PRESS_TRAIN_A_V046_CAPTURE")
code = code.replace("press_train_a_v044", "press_train_a_v046")
code = code.replace("V044", "V046").replace("v044", "v046")
exec(compile(code, str(base) + "::v046", "exec"), globals(), globals())
