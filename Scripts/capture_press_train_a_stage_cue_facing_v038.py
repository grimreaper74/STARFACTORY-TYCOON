"""Use the v037 five-camera capture procedure against exact-map v038."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_stage_exterior_cues_v037.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAStageExteriorCuesCandidate_v037", "LB_PressTrainAStageCueFacingCandidate_v038")
code = code.replace("LB_PRESS_TRAIN_A_V037_CAPTURE", "LB_PRESS_TRAIN_A_V038_CAPTURE")
code = code.replace("press_train_a_v037", "press_train_a_v038")
code = code.replace("V037", "V038").replace("v037", "v038")
exec(compile(code, str(base) + "::v038", "exec"), globals(), globals())
