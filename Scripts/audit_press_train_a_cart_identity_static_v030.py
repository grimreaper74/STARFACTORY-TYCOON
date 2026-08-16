"""Exact-map v030 adapter over the fully expanded v029 static gate."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_cart_mechanical_evidence_static_v029.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainACartMechanicalEvidenceCandidate_v029", "LB_PressTrainACartIdentityCandidate_v030")
code = code.replace("press_train_a_cart_mechanical_evidence_static_v029.json", "press_train_a_cart_identity_static_v030.json")
code = code.replace("cart-mechanical-evidence-static-v029", "cart-identity-static-v030")
code = code.replace("PRESS_TRAIN_A_V029", "PRESS_TRAIN_A_V030")
code = code.replace("LB.Asset.Candidate.v029", "LB.Asset.Candidate.v030")
exec(compile(code, str(base) + "::v030", "exec"), globals(), globals())
