"""Use v051's five-camera capture procedure against exact-map v052."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_crown_endpoint_refinement_v051.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainACrownEndpointRefinementCandidate_v051", "LB_PressTrainADieChangeCameraEvidenceCandidate_v052")
code = code.replace("LB_PRESS_TRAIN_A_V051_CAPTURE", "LB_PRESS_TRAIN_A_V052_CAPTURE")
code = code.replace("press_train_a_v051", "press_train_a_v052")
code = code.replace("V051", "V052").replace("v051", "v052")
exec(compile(code, str(base) + "::v052", "exec"), globals(), globals())
