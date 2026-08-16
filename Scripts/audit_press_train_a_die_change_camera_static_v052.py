"""Use v051's exact static gate against die-change camera map v052."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_crown_endpoint_refinement_static_v051.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainACrownEndpointRefinementCandidate_v051", "LB_PressTrainADieChangeCameraEvidenceCandidate_v052")
code = code.replace("press_train_a_crown_endpoint_refinement_static_v051", "press_train_a_die_change_camera_static_v052")
code = code.replace("crown-endpoint-refinement-static-v051", "die-change-camera-static-v052")
code = code.replace("LB.Asset.Candidate.v051", "LB.Asset.Candidate.v052")
code = code.replace("PRESS_TRAIN_A_V051", "PRESS_TRAIN_A_V052")
code = code.replace("V051", "V052").replace("v051", "v052")
exec(compile(code, str(base) + "::v052", "exec"), globals(), globals())
