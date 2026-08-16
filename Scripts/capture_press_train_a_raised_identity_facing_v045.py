"""Use v044's five-camera capture procedure against exact-map v045."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_raised_identity_v044.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainARaisedIdentityCandidate_v044", "LB_PressTrainARaisedIdentityFacingCandidate_v045")
code = code.replace("LB_PRESS_TRAIN_A_V044_CAPTURE", "LB_PRESS_TRAIN_A_V045_CAPTURE")
code = code.replace("press_train_a_v044", "press_train_a_v045")
code = code.replace("V044", "V045").replace("v044", "v045")
exec(compile(code, str(base) + "::v045", "exec"), globals(), globals())
