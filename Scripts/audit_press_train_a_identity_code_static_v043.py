"""Use v041's exact static gate against stage-code map v043."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_physical_identity_static_v041.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAPhysicalIdentityCandidate_v041", "LB_PressTrainAIdentityCodeCandidate_v043")
code = code.replace("press_train_a_physical_identity_static_v041", "press_train_a_identity_code_static_v043")
code = code.replace("physical-identity-static-v041", "identity-code-static-v043")
code = code.replace("LB.Asset.Candidate.v041", "LB.Asset.Candidate.v043")
code = code.replace("PRESS_TRAIN_A_V041", "PRESS_TRAIN_A_V043")
code = code.replace("v041", "v043").replace("V041", "V043")
exec(compile(code, str(base) + "::v043", "exec"), globals(), globals())
