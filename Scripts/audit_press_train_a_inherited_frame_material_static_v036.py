"""Exact-map v036 adapter over the v035 static gate."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_facade_material_static_v035.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_PressTrainAFacadeMaterialCandidate_v035", "LB_PressTrainAInheritedFrameMaterialCandidate_v036")
code = code.replace("press_train_a_facade_material_static_v035.json", "press_train_a_inherited_frame_material_static_v036.json")
code = code.replace("facade-material-static-v035", "inherited-frame-material-static-v036")
code = code.replace("PRESS_TRAIN_A_V035", "PRESS_TRAIN_A_V036")
code = code.replace("LB.Asset.Candidate.v035", "LB.Asset.Candidate.v036")
exec(compile(code, str(base) + "::v036", "exec"), globals(), globals())
