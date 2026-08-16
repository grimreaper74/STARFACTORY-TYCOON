"""Build v066 directly from v053 with copied access materials and die-side flow-axis endpoint cameras."""

from pathlib import Path


base = Path(__file__).with_name("build_press_train_a_endpoint_evidence_candidate_v064.py")
code = base.read_text(encoding="utf-8")
code = code.replace("import_build_press_train_a_dock_coupling_candidate_v064.py", "import_build_press_train_a_dock_coupling_candidate_v066.py")
code = code.replace("CA_MW_PTA_CAM_S01FeedEvidence_v064", "CA_MW_PTA_CAM_S01DieSideFlow_v066")
code = code.replace("CA_MW_PTA_CAM_S07DischargeEvidence_v064", "CA_MW_PTA_CAM_S07DieSideFlow_v066")
code = code.replace("unreal.Vector(-920.0, -520.0, 330.0)", "unreal.Vector(900.0, -650.0, 340.0)")
code = code.replace("unreal.Vector(-190.0, 90.0, 150.0)", "unreal.Vector(0.0, -100.0, 140.0)")
code = code.replace("unreal.Vector(-940.0, 5120.0, 350.0)", "unreal.Vector(1000.0, 5350.0, 360.0)")
code = code.replace("unreal.Vector(-300.0, 4230.0, 230.0)", "unreal.Vector(0.0, 4850.0, 155.0)")
code = code.replace("EndpointEvidence.v064", "EndpointDieSideFlow.v066")
code = code.replace("endpoint_evidence_v064", "die_side_endpoint_v066")
code = code.replace("endpoint-evidence-v064", "die-side-endpoint-v066")
code = code.replace("Candidate_v064", "Candidate_v066")
code = code.replace("LB.Asset.Candidate.v064", "LB.Asset.Candidate.v066")
code = code.replace("PRESS_TRAIN_A_V064", "PRESS_TRAIN_A_V066")
code = code.replace("V064", "V066").replace("v064", "v066")
exec(compile(code, str(base) + "::v066", "exec"), globals(), globals())
