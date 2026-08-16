"""Use the v035 capture procedure against exact-map v036."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_facade_material_v035.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAFacadeMaterialCandidate_v035", "LB_PressTrainAInheritedFrameMaterialCandidate_v036")
code = code.replace("LB_PRESS_TRAIN_A_V035_CAPTURE", "LB_PRESS_TRAIN_A_V036_CAPTURE")
code = code.replace("press_train_a_v035", "press_train_a_v036")
code = code.replace("V035", "V036")
code = code.replace("v035", "v036")
exec(compile(code, str(base) + "::v036", "exec"), globals(), globals())
