"""Exact-map v032 adapter over the v031 static gate."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_cart_legibility_static_v031.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainACartLegibilityCandidate_v031", "LB_PressTrainACartPlateClearanceCandidate_v032")
code = code.replace("press_train_a_cart_legibility_static_v031.json", "press_train_a_cart_plate_clearance_static_v032.json")
code = code.replace("cart-legibility-static-v031", "cart-plate-clearance-static-v032")
code = code.replace("PRESS_TRAIN_A_V031", "PRESS_TRAIN_A_V032")
code = code.replace("LB.Asset.Candidate.v031", "LB.Asset.Candidate.v032")
exec(compile(code, str(base) + "::v032", "exec"), globals(), globals())
