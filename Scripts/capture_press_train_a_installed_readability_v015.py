"""v015 fixed-camera adapter for installed-readability visual gate."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_isolated_v001.py")
code = base.read_text(encoding="utf-8")
code = code.replace("/Game/LineBoss/Maps/LB_PressTrainAIsolatedCandidate_v001", "/Game/LineBoss/Maps/LB_PressTrainAInstalledReadabilityCandidate_v015")
code = code.replace("LB_PRESS_TRAIN_A_V001_CAPTURE", "LB_PRESS_TRAIN_A_V015_CAPTURE")
code = code.replace("Press Train A v001", "Press Train A v015")
code = code.replace("press_train_a_v001", "press_train_a_v015")
code = code.replace("PRESS_TRAIN_A_V001_CAPTURE", "PRESS_TRAIN_A_V015_CAPTURE")
exec(compile(code, str(base) + "::v015", "exec"), globals(), globals())
