"""Capture all four fixed cameras from exact Train A v026."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_material_calibration_v025.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAMaterialCalibrationCandidate_v025", "LB_PressTrainAExteriorDetailCandidate_v026")
code = code.replace("V025", "V026")
code = code.replace("v025", "v026")
exec(compile(code, str(base) + "::v026", "exec"), globals(), globals())
