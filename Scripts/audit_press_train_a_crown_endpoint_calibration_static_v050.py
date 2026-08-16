"""Use v049's exact static gate against calibrated map v050."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_crown_endpoint_clearance_static_v049.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainACrownEndpointClearanceCandidate_v049", "LB_PressTrainACrownEndpointCalibrationCandidate_v050")
code = code.replace("press_train_a_crown_endpoint_clearance_static_v049", "press_train_a_crown_endpoint_calibration_static_v050")
code = code.replace("crown-endpoint-clearance-static-v049", "crown-endpoint-calibration-static-v050")
code = code.replace("LB.Asset.Candidate.v049", "LB.Asset.Candidate.v050")
code = code.replace("PRESS_TRAIN_A_V049", "PRESS_TRAIN_A_V050")
code = code.replace("V049", "V050").replace("v049", "v050")
exec(compile(code, str(base) + "::v050", "exec"), globals(), globals())
