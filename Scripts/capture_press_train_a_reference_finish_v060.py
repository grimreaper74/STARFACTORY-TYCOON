"""Use the established five fixed cameras against exact-map v060."""

from pathlib import Path


base = Path(__file__).with_name("capture_press_train_a_reference_finish_v058.py")
code = base.read_text(encoding="utf-8")
code = code.replace("Candidate_v058", "Candidate_v060")
code = code.replace("LB_PRESS_TRAIN_A_V058_CAPTURE", "LB_PRESS_TRAIN_A_V060_CAPTURE")
code = code.replace("press_train_a_v058", "press_train_a_v060")
code = code.replace("V058", "V060").replace("v058", "v060")
exec(compile(code, str(base) + "::v060", "exec"), globals(), globals())
