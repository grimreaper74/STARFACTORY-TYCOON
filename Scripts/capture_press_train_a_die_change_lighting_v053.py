"""Use v051's five-camera capture procedure against exact-map v053."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_crown_endpoint_refinement_v051.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainACrownEndpointRefinementCandidate_v051", "LB_PressTrainADieChangeLightingCalibrationCandidate_v053")
code = code.replace("LB_PRESS_TRAIN_A_V051_CAPTURE", "LB_PRESS_TRAIN_A_V053_CAPTURE")
code = code.replace("press_train_a_v051", "press_train_a_v053")
code = code.replace("V051", "V053").replace("v051", "v053")
exec(compile(code, str(base) + "::v053", "exec"), globals(), globals())
