"""Capture all four retained fixed cameras from exact Train A v023."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_die_change_evidence_v022.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainADieChangeEvidenceCandidate_v022", "LB_PressTrainAReleaseDetailCandidate_v023")
code = code.replace("V022", "V023")
code = code.replace("v022", "v023")
exec(compile(code, str(base) + "::v023", "exec"), globals(), globals())
