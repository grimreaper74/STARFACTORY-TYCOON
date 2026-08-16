"""v014 exact-map static audit adapter."""

from pathlib import Path


base = Path(__file__).with_name("audit_press_train_a_stage_detail_static_v013.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAStageDetailCandidate_v013", "LB_PressTrainACCTVMaterialCandidate_v014")
code = code.replace("StageDetail_v001", "StageDetail_v002")
code = code.replace("_v001", "_v002")
code = code.replace("MechanicalBay_v002/SM_CA_MW_PT_MechanicalBayDress_v002", "MechanicalBay_v001/SM_CA_MW_PT_MechanicalBayDress_v001")
code = code.replace("press_train_a_stage_detail_static_v013.json", "press_train_a_cctv_material_static_v014.json")
code = code.replace("stage-detail-static-v013", "cctv-material-static-v014")
code = code.replace("PRESS_TRAIN_A_V013", "PRESS_TRAIN_A_V014")
code = code.replace("LB.Asset.Candidate.v013", "LB.Asset.Candidate.v014")
code = code.replace("candidate_v013", "candidate_v014")
code = code.replace("v013 candidate tag", "v014 candidate tag")
exec(compile(code, str(base) + "::v014", "exec"), globals(), globals())
