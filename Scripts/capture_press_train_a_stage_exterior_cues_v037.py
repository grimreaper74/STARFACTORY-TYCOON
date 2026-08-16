"""Use the v036 five-camera capture procedure against exact-map v037."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_inherited_frame_material_v036.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAInheritedFrameMaterialCandidate_v036", "LB_PressTrainAStageExteriorCuesCandidate_v037")
code = code.replace("LB_PRESS_TRAIN_A_V036_CAPTURE", "LB_PRESS_TRAIN_A_V037_CAPTURE")
code = code.replace("press_train_a_v036", "press_train_a_v037")
code = code.replace("V036", "V037").replace("v036", "v037")
exec(compile(code, str(base) + "::v037", "exec"), globals(), globals())
