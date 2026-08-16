"""Build the clean v062 successor from retained v053."""

from pathlib import Path


base = Path(__file__).with_name("build_press_train_a_industrial_readability_candidate_v061.py")
code = base.read_text(encoding="utf-8")
code = code.replace("import_build_press_train_a_dock_coupling_candidate_v061.py", "import_build_press_train_a_dock_coupling_candidate_v062.py")
code = code.replace("Candidate_v061", "Candidate_v062")
code = code.replace("industrial_readability_v061", "industrial_readability_v062")
code = code.replace("industrial-readability-v061", "industrial-readability-v062")
code = code.replace("IndustrialReadability.v061", "IndustrialReadability.v062")
code = code.replace("LB.Asset.Candidate.v061", "LB.Asset.Candidate.v062")
code = code.replace("PRESS_TRAIN_A_V061", "PRESS_TRAIN_A_V062")
code = code.replace("V061", "V062").replace("v061", "v062")
exec(compile(code, str(base) + "::v062", "exec"), globals(), globals())
