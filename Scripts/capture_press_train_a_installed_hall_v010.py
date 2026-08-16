"""v010 fixed-camera adapter for Train A installed-hall visual gate."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_isolated_v001.py")
code = base.read_text(encoding="utf-8")
code = code.replace("/Game/LineBoss/Maps/LB_PressTrainAIsolatedCandidate_v001", "/Game/LineBoss/Maps/LB_PressTrainAInstalledHallCandidate_v010")
code = code.replace("LB_PRESS_TRAIN_A_V001_CAPTURE", "LB_PRESS_TRAIN_A_V010_CAPTURE")
code = code.replace("Press Train A v001", "Press Train A v010")
code = code.replace("press_train_a_v001", "press_train_a_v010")
code = code.replace("PRESS_TRAIN_A_V001_CAPTURE", "PRESS_TRAIN_A_V010_CAPTURE")
exec(compile(code, str(base) + "::v010", "exec"), globals(), globals())
