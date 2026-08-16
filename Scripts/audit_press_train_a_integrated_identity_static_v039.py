"""Use v038's exact static gate against integrated-identity map v039."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_stage_cue_facing_static_v038.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAStageCueFacingCandidate_v038", "LB_PressTrainAIntegratedIdentityCandidate_v039")
code = code.replace("press_train_a_stage_cue_facing_static_v038", "press_train_a_integrated_identity_static_v039")
code = code.replace("stage-cue-facing-static-v038", "integrated-identity-static-v039")
code = code.replace("LB.Asset.Candidate.v038", "LB.Asset.Candidate.v039")
code = code.replace("PRESS_TRAIN_A_V038", "PRESS_TRAIN_A_V039")
code = code.replace("v038", "v039").replace("V038", "V039")
exec(compile(code, str(base) + "::v039", "exec"), globals(), globals())
