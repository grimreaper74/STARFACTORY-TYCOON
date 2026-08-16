"""Capture all four fixed cameras from exact Train A v025."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_release_presentation_v024.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAReleasePresentationCandidate_v024", "LB_PressTrainAMaterialCalibrationCandidate_v025")
code = code.replace("V024", "V025")
code = code.replace("v024", "v025")
exec(compile(code, str(base) + "::v025", "exec"), globals(), globals())
