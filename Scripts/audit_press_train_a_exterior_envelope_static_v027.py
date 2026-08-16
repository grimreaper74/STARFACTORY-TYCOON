"""Static audit adapter for corrected exterior-envelope v027."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_exterior_detail_static_v026.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAExteriorDetailCandidate_v026", "LB_PressTrainAExteriorEnvelopeCandidate_v027")
code = code.replace("press_train_a_exterior_detail_static_v026.json", "press_train_a_exterior_envelope_static_v027.json")
code = code.replace("exterior-detail-static-v026", "exterior-envelope-static-v027")
code = code.replace("PRESS_TRAIN_A_V026", "PRESS_TRAIN_A_V027")
code = code.replace("LB.Asset.Candidate.v026", "LB.Asset.Candidate.v027")
exec(compile(code, str(base) + "::v027", "exec"), globals(), globals())
