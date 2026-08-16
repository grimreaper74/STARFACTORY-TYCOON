"""Exact-map v035 adapter over the v034 static gate."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_facade_lighting_static_v034.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAFacadeLightingCandidate_v034", "LB_PressTrainAFacadeMaterialCandidate_v035")
code = code.replace("press_train_a_facade_lighting_static_v034.json", "press_train_a_facade_material_static_v035.json")
code = code.replace("facade-lighting-static-v034", "facade-material-static-v035")
code = code.replace("PRESS_TRAIN_A_V034", "PRESS_TRAIN_A_V035")
code = code.replace("LB.Asset.Candidate.v034", "LB.Asset.Candidate.v035")
exec(compile(code, str(base) + "::v035", "exec"), globals(), globals())
