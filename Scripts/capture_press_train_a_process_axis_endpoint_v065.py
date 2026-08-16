"""Capture one of seven exact-map Train A v065 views per Unreal process."""

from pathlib import Path


base = Path(__file__).with_name("capture_press_train_a_endpoint_evidence_v064.py")
code = base.read_text(encoding="utf-8")
code = code.replace("CA_MW_PTA_CAM_S01FeedEvidence_v064", "CA_MW_PTA_CAM_S01ProcessAxis_v065")
code = code.replace("CA_MW_PTA_CAM_S07DischargeEvidence_v064", "CA_MW_PTA_CAM_S07ProcessAxis_v065")
code = code.replace("endpoint_evidence_v064", "process_axis_endpoint_v065")
code = code.replace("LB_PRESS_TRAIN_A_V064_CAPTURE", "LB_PRESS_TRAIN_A_V065_CAPTURE")
code = code.replace("press_train_a_v064", "press_train_a_v065")
code = code.replace("Candidate_v064", "Candidate_v065")
code = code.replace("PRESS_TRAIN_A_V064", "PRESS_TRAIN_A_V065")
code = code.replace("V064", "V065").replace("v064", "v065")
exec(compile(code, str(base) + "::v065", "exec"), globals(), globals())
