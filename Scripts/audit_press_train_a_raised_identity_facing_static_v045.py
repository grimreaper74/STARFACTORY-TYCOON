"""Use v044's exact static gate against corrected plate-facing map v045."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_raised_identity_static_v044.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainARaisedIdentityCandidate_v044", "LB_PressTrainARaisedIdentityFacingCandidate_v045")
code = code.replace("press_train_a_raised_identity_static_v044", "press_train_a_raised_identity_facing_static_v045")
code = code.replace("raised-identity-static-v044", "raised-identity-facing-static-v045")
code = code.replace("LB.Asset.Candidate.v044", "LB.Asset.Candidate.v045")
code = code.replace("PRESS_TRAIN_A_V044", "PRESS_TRAIN_A_V045")
code = code.replace("v044", "v045").replace("V044", "V045")
exec(compile(code, str(base) + "::v045", "exec"), globals(), globals())
