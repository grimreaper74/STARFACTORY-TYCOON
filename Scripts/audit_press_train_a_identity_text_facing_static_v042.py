"""Use v041's exact static gate against identity-text-facing map v042."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_physical_identity_static_v041.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAPhysicalIdentityCandidate_v041", "LB_PressTrainAIdentityTextFacingCandidate_v042")
code = code.replace("press_train_a_physical_identity_static_v041", "press_train_a_identity_text_facing_static_v042")
code = code.replace("physical-identity-static-v041", "identity-text-facing-static-v042")
code = code.replace("LB.Asset.Candidate.v041", "LB.Asset.Candidate.v042")
code = code.replace("PRESS_TRAIN_A_V041", "PRESS_TRAIN_A_V042")
code = code.replace("v041", "v042").replace("V041", "V042")
exec(compile(code, str(base) + "::v042", "exec"), globals(), globals())
