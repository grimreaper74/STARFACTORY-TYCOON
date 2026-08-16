"""Use the v033 capture procedure against exact-map v034."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_enclosed_facade_v033.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAEnclosedFacadeCandidate_v033", "LB_PressTrainAFacadeLightingCandidate_v034")
code = code.replace("LB_PRESS_TRAIN_A_V033_CAPTURE", "LB_PRESS_TRAIN_A_V034_CAPTURE")
code = code.replace("press_train_a_v033", "press_train_a_v034")
code = code.replace("V033", "V034")
code = code.replace("v033", "v034")
exec(compile(code, str(base) + "::v034", "exec"), globals(), globals())
