"""Use v048's five-camera capture procedure against exact-map v049."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_crown_endpoint_v048.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainACrownEndpointCandidate_v048", "LB_PressTrainACrownEndpointClearanceCandidate_v049")
code = code.replace("LB_PRESS_TRAIN_A_V048_CAPTURE", "LB_PRESS_TRAIN_A_V049_CAPTURE")
code = code.replace("press_train_a_v048", "press_train_a_v049")
code = code.replace("V048", "V049").replace("v048", "v049")
exec(compile(code, str(base) + "::v049", "exec"), globals(), globals())
