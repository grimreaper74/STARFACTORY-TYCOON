"""Build v065 directly from v053 with copied access materials and process-axis endpoint cameras."""

from pathlib import Path


base = Path(__file__).with_name("build_press_train_a_endpoint_evidence_candidate_v064.py")
code = base.read_text(encoding="utf-8")
code = code.replace("import_build_press_train_a_dock_coupling_candidate_v064.py", "import_build_press_train_a_dock_coupling_candidate_v065.py")
code = code.replace("CA_MW_PTA_CAM_S01FeedEvidence_v064", "CA_MW_PTA_CAM_S01ProcessAxis_v065")
code = code.replace("CA_MW_PTA_CAM_S07DischargeEvidence_v064", "CA_MW_PTA_CAM_S07ProcessAxis_v065")
code = code.replace("unreal.Vector(-920.0, -520.0, 330.0)", "unreal.Vector(0.0, -600.0, 280.0)")
code = code.replace("unreal.Vector(-190.0, 90.0, 150.0)", "unreal.Vector(0.0, -70.0, 135.0)")
code = code.replace("unreal.Vector(-940.0, 5120.0, 350.0)", "unreal.Vector(0.0, 5450.0, 285.0)")
code = code.replace("unreal.Vector(-300.0, 4230.0, 230.0)", "unreal.Vector(0.0, 4820.0, 150.0)")
code = code.replace("EndpointEvidence.v064", "EndpointProcessAxis.v065")
code = code.replace("endpoint_evidence_v064", "process_axis_endpoint_v065")
code = code.replace("endpoint-evidence-v064", "process-axis-endpoint-v065")
code = code.replace("Candidate_v064", "Candidate_v065")
code = code.replace("LB.Asset.Candidate.v064", "LB.Asset.Candidate.v065")
code = code.replace("PRESS_TRAIN_A_V064", "PRESS_TRAIN_A_V065")
code = code.replace("V064", "V065").replace("v064", "v065")
exec(compile(code, str(base) + "::v065", "exec"), globals(), globals())
