"""Run the v037 exact gate with v041's seven physical identity plates."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_stage_exterior_cues_static_v037.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAStageExteriorCuesCandidate_v037", "LB_PressTrainAPhysicalIdentityCandidate_v041")
code = code.replace("press_train_a_stage_exterior_cues_static_v037", "press_train_a_physical_identity_static_v041")
code = code.replace("stage-exterior-cues-static-v037", "physical-identity-static-v041")
code = code.replace("LB.Asset.Candidate.v037", "LB.Asset.Candidate.v041")
code = code.replace("PRESS_TRAIN_A_V037", "PRESS_TRAIN_A_V041")
code = code.replace('"presentation": (len(presentation), 121)', '"presentation": (len(presentation), 128)')
code = code.replace("if len(scope) != 173:", "if len(scope) != 180:")
code = code.replace("expected 173 scoped actors", "expected 180 scoped actors")
code = code.replace("V037", "V041").replace("v037", "v041")
exec(compile(code, str(base) + "::v041", "exec"), globals(), globals())
