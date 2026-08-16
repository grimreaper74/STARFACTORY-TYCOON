"""Use v051's exact static gate against v054 and require v003 source bindings."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_crown_endpoint_refinement_static_v051.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainACrownEndpointRefinementCandidate_v051", "LB_PressTrainAEndpointMaterialStateCandidate_v054")
code = code.replace("press_train_a_crown_endpoint_refinement_static_v051", "press_train_a_endpoint_material_state_static_v054")
code = code.replace("crown-endpoint-refinement-static-v051", "endpoint-material-state-static-v054")
code = code.replace("LB.Asset.Candidate.v051", "LB.Asset.Candidate.v054")
code = code.replace("CrownEndpointPresentation_v002", "CrownEndpointPresentation_v003")
code = code.replace("_v002", "_v003")
code = code.replace("V002", "V003").replace("v002", "v003")
code = code.replace("PRESS_TRAIN_A_V051", "PRESS_TRAIN_A_V054")
code = code.replace("V051", "V054").replace("v051", "v054")
exec(compile(code, str(base) + "::v054", "exec"), globals(), globals())
