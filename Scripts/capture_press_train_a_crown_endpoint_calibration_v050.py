"""Use v049's five-camera capture procedure against exact-map v050."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_crown_endpoint_clearance_v049.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainACrownEndpointClearanceCandidate_v049", "LB_PressTrainACrownEndpointCalibrationCandidate_v050")
code = code.replace("LB_PRESS_TRAIN_A_V049_CAPTURE", "LB_PRESS_TRAIN_A_V050_CAPTURE")
code = code.replace("press_train_a_v049", "press_train_a_v050")
code = code.replace("V049", "V050").replace("v049", "v050")
exec(compile(code, str(base) + "::v050", "exec"), globals(), globals())
