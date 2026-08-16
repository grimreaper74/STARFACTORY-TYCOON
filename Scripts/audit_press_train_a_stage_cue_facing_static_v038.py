"""Use the v037 exact static gate against corrected cue-facing map v038."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_stage_exterior_cues_static_v037.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAStageExteriorCuesCandidate_v037", "LB_PressTrainAStageCueFacingCandidate_v038")
code = code.replace("press_train_a_stage_exterior_cues_static_v037", "press_train_a_stage_cue_facing_static_v038")
code = code.replace("stage-exterior-cues-static-v037", "stage-cue-facing-static-v038")
code = code.replace("LB.Asset.Candidate.v037", "LB.Asset.Candidate.v038")
code = code.replace("PRESS_TRAIN_A_V037", "PRESS_TRAIN_A_V038")
code = code.replace("v037", "v038").replace("V037", "V038")
exec(compile(code, str(base) + "::v038", "exec"), globals(), globals())
