"""Use v046's exact static gate against S07-clearance map v047."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_segmented_identity_static_v046.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainASegmentedIdentityCandidate_v046", "LB_PressTrainAS07IdentityClearanceCandidate_v047")
code = code.replace("press_train_a_segmented_identity_static_v046", "press_train_a_s07_identity_clearance_static_v047")
code = code.replace("segmented-identity-static-v046", "s07-identity-clearance-static-v047")
code = code.replace("LB.Asset.Candidate.v046", "LB.Asset.Candidate.v047")
code = code.replace("PRESS_TRAIN_A_V046", "PRESS_TRAIN_A_V047")
code = code.replace("v046", "v047").replace("V046", "V047")
exec(compile(code, str(base) + "::v047", "exec"), globals(), globals())
