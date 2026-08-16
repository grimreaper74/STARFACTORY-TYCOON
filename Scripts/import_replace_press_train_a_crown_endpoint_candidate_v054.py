"""Import warning-clean crown/endpoint v003 and replace v053's seven presentation actors in place."""

from pathlib import Path

base = Path(__file__).with_name("import_replace_press_train_a_crown_endpoint_candidate_v051.py")
code = base.read_text(encoding="utf-8")
code = code.replace("v002", "v003").replace("V002", "V003")
code = code.replace(
    "/Game/LineBoss/Maps/LB_PressTrainACrownEndpointCalibrationCandidate_v050",
    "/Game/LineBoss/Maps/LB_PressTrainADieChangeLightingCalibrationCandidate_v053",
)
code = code.replace(
    "/Game/LineBoss/Maps/LB_PressTrainACrownEndpointRefinementCandidate_v051",
    "/Game/LineBoss/Maps/LB_PressTrainAEndpointMaterialStateCandidate_v054",
)
code = code.replace("press_train_a_crown_endpoint_refinement_v051", "press_train_a_endpoint_material_state_v054")
code = code.replace("crown-endpoint-refinement-v051", "endpoint-material-state-v054")
code = code.replace("LB.Asset.Candidate.v051", "LB.Asset.Candidate.v054")
code = code.replace("create v051 from v050", "create v054 from v053")
code = code.replace("save v051 crown/endpoint refinement candidate", "save v054 endpoint material-state candidate")
code = code.replace("PRESS_TRAIN_A_V051", "PRESS_TRAIN_A_V054")
code = code.replace("V051", "V054").replace("v051", "v054")
exec(compile(code, str(base) + "::v054", "exec"), globals(), globals())
