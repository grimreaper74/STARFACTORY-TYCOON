"""Run the exact static/material/process-axis-camera gate on isolated Train A v065."""

from pathlib import Path


base = Path(__file__).with_name("audit_press_train_a_endpoint_evidence_static_v064.py")
code = base.read_text(encoding="utf-8")
code = code.replace("CA_MW_PTA_CAM_S01FeedEvidence_v064", "CA_MW_PTA_CAM_S01ProcessAxis_v065")
code = code.replace("CA_MW_PTA_CAM_S07DischargeEvidence_v064", "CA_MW_PTA_CAM_S07ProcessAxis_v065")
code = code.replace("LB.PressTrain.EndpointEvidence.v064", "LB.PressTrain.EndpointProcessAxis.v065")
code = code.replace("endpoint_evidence_static_v064", "process_axis_endpoint_static_v065")
code = code.replace("endpoint-evidence-static-v064", "process-axis-endpoint-static-v065")
code = code.replace("Candidate_v064", "Candidate_v065")
code = code.replace("LB.Asset.Candidate.v064", "LB.Asset.Candidate.v065")
code = code.replace("PRESS_TRAIN_A_V064", "PRESS_TRAIN_A_V065")
code = code.replace("V064", "V065").replace("v064", "v065")
exec(compile(code, str(base) + "::v065", "exec"), globals(), globals())
