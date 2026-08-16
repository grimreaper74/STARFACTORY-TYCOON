"""Use v038's five-camera capture procedure against exact-map v040."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_stage_cue_facing_v038.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAStageCueFacingCandidate_v038", "LB_PressTrainAIntegratedIdentityCandidate_v040")
code = code.replace("LB_PRESS_TRAIN_A_V038_CAPTURE", "LB_PRESS_TRAIN_A_V040_CAPTURE")
code = code.replace("press_train_a_v038", "press_train_a_v040")
code = code.replace("V038", "V040").replace("v038", "v040")
exec(compile(code, str(base) + "::v040", "exec"), globals(), globals())
