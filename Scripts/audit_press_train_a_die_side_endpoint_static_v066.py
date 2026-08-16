"""Run the exact static/material/die-side-flow-camera gate on isolated Train A v066."""

from pathlib import Path


base = Path(__file__).with_name("audit_press_train_a_endpoint_evidence_static_v064.py")
code = base.read_text(encoding="utf-8")
code = code.replace("CA_MW_PTA_CAM_S01FeedEvidence_v064", "CA_MW_PTA_CAM_S01DieSideFlow_v066")
code = code.replace("CA_MW_PTA_CAM_S07DischargeEvidence_v064", "CA_MW_PTA_CAM_S07DieSideFlow_v066")
code = code.replace("LB.PressTrain.EndpointEvidence.v064", "LB.PressTrain.EndpointDieSideFlow.v066")
code = code.replace("endpoint_evidence_static_v064", "die_side_endpoint_static_v066")
code = code.replace("endpoint-evidence-static-v064", "die-side-endpoint-static-v066")
code = code.replace("Candidate_v064", "Candidate_v066")
code = code.replace("LB.Asset.Candidate.v064", "LB.Asset.Candidate.v066")
code = code.replace("PRESS_TRAIN_A_V064", "PRESS_TRAIN_A_V066")
code = code.replace("V064", "V066").replace("v064", "v066")
exec(compile(code, str(base) + "::v066", "exec"), globals(), globals())
