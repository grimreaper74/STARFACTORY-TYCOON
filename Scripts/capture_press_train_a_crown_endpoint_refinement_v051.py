"""Use v050's five-camera capture procedure against exact-map v051."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_crown_endpoint_calibration_v050.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainACrownEndpointCalibrationCandidate_v050", "LB_PressTrainACrownEndpointRefinementCandidate_v051")
code = code.replace("LB_PRESS_TRAIN_A_V050_CAPTURE", "LB_PRESS_TRAIN_A_V051_CAPTURE")
code = code.replace("press_train_a_v050", "press_train_a_v051")
code = code.replace("V050", "V051").replace("v050", "v051")
exec(compile(code, str(base) + "::v051", "exec"), globals(), globals())
