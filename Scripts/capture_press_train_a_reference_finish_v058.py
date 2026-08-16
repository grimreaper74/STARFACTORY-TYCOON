"""Use the established five fixed cameras against exact-map v058."""

from pathlib import Path


base = Path(__file__).with_name("capture_press_train_a_dock_coupling_v057.py")
code = base.read_text(encoding="utf-8")
code = code.replace("Candidate_v057", "Candidate_v058")
code = code.replace("LB_PRESS_TRAIN_A_V057_CAPTURE", "LB_PRESS_TRAIN_A_V058_CAPTURE")
code = code.replace("press_train_a_v057", "press_train_a_v058")
code = code.replace("V057", "V058").replace("v057", "v058")
exec(compile(code, str(base) + "::v058", "exec"), globals(), globals())
