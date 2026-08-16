"""v012 fixed-camera adapter for Train A management-camera visual gate."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_isolated_v001.py")
code = base.read_text(encoding="utf-8")
code = code.replace("/Game/LineBoss/Maps/LB_PressTrainAIsolatedCandidate_v001", "/Game/LineBoss/Maps/LB_PressTrainAManagementCameraCandidate_v012")
code = code.replace("LB_PRESS_TRAIN_A_V001_CAPTURE", "LB_PRESS_TRAIN_A_V012_CAPTURE")
code = code.replace("Press Train A v001", "Press Train A v012")
code = code.replace("press_train_a_v001", "press_train_a_v012")
code = code.replace("PRESS_TRAIN_A_V001_CAPTURE", "PRESS_TRAIN_A_V012_CAPTURE")
exec(compile(code, str(base) + "::v012", "exec"), globals(), globals())
