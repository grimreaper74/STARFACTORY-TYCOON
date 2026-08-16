"""Use the established five fixed cameras against exact-map v062."""

from pathlib import Path


base = Path(__file__).with_name("capture_press_train_a_reference_finish_v060.py")
code = base.read_text(encoding="utf-8")
code = code.replace("Candidate_v060", "Candidate_v062")
code = code.replace("LB_PRESS_TRAIN_A_V060_CAPTURE", "LB_PRESS_TRAIN_A_V062_CAPTURE")
code = code.replace("press_train_a_v060", "press_train_a_v062")
code = code.replace("V060", "V062").replace("v060", "v062")
exec(compile(code, str(base) + "::v062", "exec"), globals(), globals())
