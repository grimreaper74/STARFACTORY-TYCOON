"""Use v054's exact machinery gate against v055's installed validation bay."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_endpoint_material_state_static_v054.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAEndpointMaterialStateCandidate_v054", "LB_PressTrainAInstalledBayContextCandidate_v055")
code = code.replace("press_train_a_endpoint_material_state_static_v054", "press_train_a_installed_bay_context_static_v055")
code = code.replace("endpoint-material-state-static-v054", "installed-bay-context-static-v055")
code = code.replace("LB.Asset.Candidate.v054", "LB.Asset.Candidate.v055")
code = code.replace("PRESS_TRAIN_A_V054", "PRESS_TRAIN_A_V055")
code = code.replace("V054", "V055").replace("v054", "v055")
exec(compile(code, str(base) + "::v055", "exec"), globals(), globals())
