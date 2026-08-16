"""Static audit adapter for material-calibration v025."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_release_presentation_static_v024.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAReleasePresentationCandidate_v024", "LB_PressTrainAMaterialCalibrationCandidate_v025")
code = code.replace("press_train_a_release_presentation_static_v024.json", "press_train_a_material_calibration_static_v025.json")
code = code.replace("release-presentation-static-v024", "material-calibration-static-v025")
code = code.replace("PRESS_TRAIN_A_V024", "PRESS_TRAIN_A_V025")
code = code.replace("LB.Asset.Candidate.v024", "LB.Asset.Candidate.v025")
exec(compile(code, str(base) + "::v025", "exec"), globals(), globals())
