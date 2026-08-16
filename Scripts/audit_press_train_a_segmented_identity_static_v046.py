"""Use v044's exact static count gate against segmented-identity map v046."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_raised_identity_static_v044.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainARaisedIdentityCandidate_v044", "LB_PressTrainASegmentedIdentityCandidate_v046")
code = code.replace("press_train_a_raised_identity_static_v044", "press_train_a_segmented_identity_static_v046")
code = code.replace("raised-identity-static-v044", "segmented-identity-static-v046")
code = code.replace("LB.Asset.Candidate.v044", "LB.Asset.Candidate.v046")
code = code.replace("PRESS_TRAIN_A_V044", "PRESS_TRAIN_A_V046")
code = code.replace("V044", "V046").replace("v044", "v046")
exec(compile(code, str(base) + "::v046", "exec"), globals(), globals())
