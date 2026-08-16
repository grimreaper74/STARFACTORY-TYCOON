"""Exact-map v034 adapter over the v033 static gate."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_enclosed_facade_static_v033.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAEnclosedFacadeCandidate_v033", "LB_PressTrainAFacadeLightingCandidate_v034")
code = code.replace("press_train_a_enclosed_facade_static_v033.json", "press_train_a_facade_lighting_static_v034.json")
code = code.replace("enclosed-facade-static-v033", "facade-lighting-static-v034")
code = code.replace("PRESS_TRAIN_A_V033", "PRESS_TRAIN_A_V034")
code = code.replace("LB.Asset.Candidate.v033", "LB.Asset.Candidate.v034")
code = code.replace("if len(scope) != 164:", "if len(scope) != 169:")
code = code.replace("expected 164 scoped actors", "expected 169 scoped actors")
exec(compile(code, str(base) + "::v034", "exec"), globals(), globals())
