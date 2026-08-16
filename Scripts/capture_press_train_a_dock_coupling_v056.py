"""Use v053's five-camera procedure against exact-map v056."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_die_change_lighting_v053.py")
code = base.read_text(encoding="utf-8")
code = code.replace(
    "LB_PressTrainADieChangeLightingCalibrationCandidate_v053",
    "LB_PressTrainADockCouplingEvidenceCandidate_v056",
)
code = code.replace("LB_PRESS_TRAIN_A_V053_CAPTURE", "LB_PRESS_TRAIN_A_V056_CAPTURE")
code = code.replace("press_train_a_v053", "press_train_a_v056")
code = code.replace("V053", "V056").replace("v053", "v056")
exec(compile(code, str(base) + "::v056", "exec"), globals(), globals())
