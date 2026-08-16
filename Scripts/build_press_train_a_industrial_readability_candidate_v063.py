"""Build v063 from retained v053 with corrected access-module yaw."""

from pathlib import Path


base = Path(__file__).with_name("build_press_train_a_industrial_readability_candidate_v061.py")
code = base.read_text(encoding="utf-8")
code = code.replace("import_build_press_train_a_dock_coupling_candidate_v061.py", "import_build_press_train_a_dock_coupling_candidate_v063.py")
code = code.replace("unreal.Rotator(0.0, 180.0, 0.0)", "unreal.Rotator(0.0, 0.0, 180.0)")
code = code.replace("Candidate_v061", "Candidate_v063")
code = code.replace("industrial_readability_v061", "industrial_readability_v063")
code = code.replace("industrial-readability-v061", "industrial-readability-v063")
code = code.replace("IndustrialReadability.v061", "IndustrialReadability.v063")
code = code.replace("LB.Asset.Candidate.v061", "LB.Asset.Candidate.v063")
code = code.replace("PRESS_TRAIN_A_V061", "PRESS_TRAIN_A_V063")
code = code.replace("V061", "V063").replace("v061", "v063")
exec(compile(code, str(base) + "::v063", "exec"), globals(), globals())
