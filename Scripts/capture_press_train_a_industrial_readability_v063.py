"""Use the established five fixed cameras against exact-map v063."""

from pathlib import Path


base = Path(__file__).with_name("capture_press_train_a_industrial_readability_v062.py")
code = base.read_text(encoding="utf-8")
code = code.replace("Candidate_v062", "Candidate_v063")
code = code.replace("LB_PRESS_TRAIN_A_V062_CAPTURE", "LB_PRESS_TRAIN_A_V063_CAPTURE")
code = code.replace("press_train_a_v062", "press_train_a_v063")
code = code.replace("V062", "V063").replace("v062", "v063")
exec(compile(code, str(base) + "::v063", "exec"), globals(), globals())
