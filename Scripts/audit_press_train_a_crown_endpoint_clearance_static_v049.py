"""Use v048's exact static gate against crown/endpoint-clearance map v049."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_crown_endpoint_static_v048.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainACrownEndpointCandidate_v048", "LB_PressTrainACrownEndpointClearanceCandidate_v049")
code = code.replace("press_train_a_crown_endpoint_static_v048", "press_train_a_crown_endpoint_clearance_static_v049")
code = code.replace("crown-endpoint-static-v048", "crown-endpoint-clearance-static-v049")
code = code.replace("LB.Asset.Candidate.v048", "LB.Asset.Candidate.v049")
code = code.replace("PRESS_TRAIN_A_V048", "PRESS_TRAIN_A_V049")
code = code.replace("V048", "V049").replace("v048", "v049")
exec(compile(code, str(base) + "::v049", "exec"), globals(), globals())
