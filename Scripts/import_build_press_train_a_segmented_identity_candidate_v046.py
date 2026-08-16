"""Adapt the verified v044 import path to explicit segmented identity source v002."""

from pathlib import Path

base = Path(__file__).with_name("import_build_press_train_a_raised_identity_candidate_v044.py")
code = base.read_text(encoding="utf-8")
code = code.replace("RaisedIdentityPlates_v001", "SegmentedIdentityPlates_v002")
code = code.replace("PRESS_TRAIN_RAISED_IDENTITY_PLATES_MANIFEST_v001", "PRESS_TRAIN_SEGMENTED_IDENTITY_PLATES_MANIFEST_v002")
code = code.replace("press_train_raised_identity_plates_source_audit_v001", "press_train_segmented_identity_plates_source_audit_v002")
code = code.replace("RaisedIdentityPlate_v001", "SegmentedIdentityPlate_v002")
code = code.replace("LB_PressTrainARaisedIdentityCandidate_v044", "LB_PressTrainASegmentedIdentityCandidate_v046")
code = code.replace("press_train_a_raised_identity_build_v044", "press_train_a_segmented_identity_build_v046")
code = code.replace("raised-identity-build-v044", "segmented-identity-build-v046")
code = code.replace("RaisedIdentityPlate", "SegmentedIdentityPlate")
code = code.replace("RAISED_IDENTITY", "SEGMENTED_IDENTITY")
code = code.replace("Raised identity", "Segmented identity")
code = code.replace("raised identity", "segmented identity")
code = code.replace("LB.Asset.Candidate.v044", "LB.Asset.Candidate.v046")
code = code.replace("V044", "V046").replace("v044", "v046")
exec(compile(code, str(base) + "::v046", "exec"), globals(), globals())
