"""Build v069 from v053 by applying v068's proven clearance within the retained 56 m envelope."""

from pathlib import Path


base = Path(__file__).with_name("build_press_train_a_endpoint_clearance_candidate_v068.py")
code = base.read_text(encoding="utf-8")
code = code.replace("import_build_press_train_a_dock_coupling_candidate_v068.py", "import_build_press_train_a_dock_coupling_candidate_v069.py")
code = code.replace("CA_MW_PTA_CAM_S01FeedClear_v068", "CA_MW_PTA_CAM_S01FeedClear_v069")
code = code.replace("CA_MW_PTA_CAM_S07DischargeClear_v068", "CA_MW_PTA_CAM_S07DischargeClear_v069")
code = code.replace("unreal.Vector(650.0, 6100.0, 900.0)", "unreal.Vector(650.0, 6000.0, 900.0)")
code = code.replace("unreal.Vector(0.0, 5000.0, 160.0)", "unreal.Vector(0.0, 4900.0, 160.0)")
code = code.replace("4550.0, \"LB.PressTrain.Stage.S07\"", "4460.0, \"LB.PressTrain.Stage.S07\"")
code = code.replace("EndpointClearance.v068", "EndpointClearance.v069")
code = code.replace("endpoint_clearance_v068", "endpoint_clearance_v069")
code = code.replace("endpoint-clearance-v068", "endpoint-clearance-v069")
code = code.replace("Candidate_v068", "Candidate_v069")
code = code.replace("LB.Asset.Candidate.v068", "LB.Asset.Candidate.v069")
code = code.replace("PRESS_TRAIN_A_V068", "PRESS_TRAIN_A_V069")
code = code.replace("V068", "V069").replace("v068", "v069")
exec(compile(code, str(base) + "::v069", "exec"), globals(), globals())
