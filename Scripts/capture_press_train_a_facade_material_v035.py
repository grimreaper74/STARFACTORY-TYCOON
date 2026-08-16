"""Use the v034 capture procedure against exact-map v035."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_facade_lighting_v034.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAFacadeLightingCandidate_v034", "LB_PressTrainAFacadeMaterialCandidate_v035")
code = code.replace("LB_PRESS_TRAIN_A_V034_CAPTURE", "LB_PRESS_TRAIN_A_V035_CAPTURE")
code = code.replace("press_train_a_v034", "press_train_a_v035")
code = code.replace("V034", "V035")
code = code.replace("v034", "v035")
exec(compile(code, str(base) + "::v035", "exec"), globals(), globals())
