"""Use v051's exact static gate against die-change lighting map v053."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_crown_endpoint_refinement_static_v051.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainACrownEndpointRefinementCandidate_v051", "LB_PressTrainADieChangeLightingCalibrationCandidate_v053")
code = code.replace("press_train_a_crown_endpoint_refinement_static_v051", "press_train_a_die_change_lighting_static_v053")
code = code.replace("crown-endpoint-refinement-static-v051", "die-change-lighting-static-v053")
code = code.replace("LB.Asset.Candidate.v051", "LB.Asset.Candidate.v053")
code = code.replace("PRESS_TRAIN_A_V051", "PRESS_TRAIN_A_V053")
code = code.replace("V051", "V053").replace("v051", "v053")
exec(compile(code, str(base) + "::v053", "exec"), globals(), globals())
