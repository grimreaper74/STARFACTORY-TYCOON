"""Capture all four fixed cameras from exact Train A v024."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_release_detail_v023.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAReleaseDetailCandidate_v023", "LB_PressTrainAReleasePresentationCandidate_v024")
code = code.replace("V023", "V024")
code = code.replace("v023", "v024")
exec(compile(code, str(base) + "::v024", "exec"), globals(), globals())
