"""Capture all four fixed cameras from exact Train A v027."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_exterior_detail_v026.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAExteriorDetailCandidate_v026", "LB_PressTrainAExteriorEnvelopeCandidate_v027")
code = code.replace("V026", "V027")
code = code.replace("v026", "v027")
exec(compile(code, str(base) + "::v027", "exec"), globals(), globals())
