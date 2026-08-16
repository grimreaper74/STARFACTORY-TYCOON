"""Exact-map v031 adapter over the v030 static gate."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_cart_identity_static_v030.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainACartIdentityCandidate_v030", "LB_PressTrainACartLegibilityCandidate_v031")
code = code.replace("press_train_a_cart_identity_static_v030.json", "press_train_a_cart_legibility_static_v031.json")
code = code.replace("cart-identity-static-v030", "cart-legibility-static-v031")
code = code.replace("PRESS_TRAIN_A_V030", "PRESS_TRAIN_A_V031")
code = code.replace("LB.Asset.Candidate.v030", "LB.Asset.Candidate.v031")
exec(compile(code, str(base) + "::v031", "exec"), globals(), globals())
