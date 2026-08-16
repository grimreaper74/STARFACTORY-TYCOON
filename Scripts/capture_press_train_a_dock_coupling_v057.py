"""Use the established five fixed cameras against exact-map v057."""

from pathlib import Path


base = Path(__file__).with_name("capture_press_train_a_dock_coupling_v056.py")
code = base.read_text(encoding="utf-8")
code = code.replace("Candidate_v056", "Candidate_v057")
code = code.replace("LB_PRESS_TRAIN_A_V056_CAPTURE", "LB_PRESS_TRAIN_A_V057_CAPTURE")
code = code.replace("press_train_a_v056", "press_train_a_v057")
code = code.replace("V056", "V057").replace("v056", "v057")
exec(compile(code, str(base) + "::v057", "exec"), globals(), globals())
