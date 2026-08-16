"""Use v054's five-camera capture procedure against exact-map v055."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_endpoint_material_state_v054.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAEndpointMaterialStateCandidate_v054", "LB_PressTrainAInstalledBayContextCandidate_v055")
code = code.replace("LB_PRESS_TRAIN_A_V054_CAPTURE", "LB_PRESS_TRAIN_A_V055_CAPTURE")
code = code.replace("press_train_a_v054", "press_train_a_v055")
code = code.replace("V054", "V055").replace("v054", "v055")
exec(compile(code, str(base) + "::v055", "exec"), globals(), globals())
