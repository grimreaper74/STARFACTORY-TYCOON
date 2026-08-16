"""Capture adapter for the isolated PR-009 v086 calibrated presentation map."""
from pathlib import Path

base = Path(__file__).with_name("capture_press_shop_pr009_layered_presentation_v085.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LayeredPresentationCandidate_v085", "LayeredPresentationCandidate_v086")
code = code.replace("layered_presentation_v085", "calibrated_presentation_v086")
code = code.replace("layered v085", "calibrated v086")
code = code.replace("V085", "V086").replace("v085", "v086")
exec(compile(code, str(base) + "::v086-capture-adapter", "exec"), globals(), globals())
