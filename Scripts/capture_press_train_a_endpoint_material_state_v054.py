"""Use v053's five-camera capture procedure against exact-map v054."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_die_change_lighting_v053.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainADieChangeLightingCalibrationCandidate_v053", "LB_PressTrainAEndpointMaterialStateCandidate_v054")
code = code.replace("LB_PRESS_TRAIN_A_V053_CAPTURE", "LB_PRESS_TRAIN_A_V054_CAPTURE")
code = code.replace("press_train_a_v053", "press_train_a_v054")
code = code.replace("V053", "V054").replace("v053", "v054")
exec(compile(code, str(base) + "::v054", "exec"), globals(), globals())
