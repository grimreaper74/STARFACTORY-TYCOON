"""Build isolated Train A v067 directly from v053 with coupling v003."""

from pathlib import Path


base = Path(__file__).with_name("import_build_press_train_a_dock_coupling_candidate_v061.py")
code = base.read_text(encoding="utf-8")
code = code.replace("Candidate_v061", "Candidate_v067")
code = code.replace("evidence_v061", "evidence_v067")
code = code.replace("candidate-v061", "candidate-v067")
code = code.replace("LB.Asset.Candidate.v061", "LB.Asset.Candidate.v067")
code = code.replace("PRESS_TRAIN_A_V061", "PRESS_TRAIN_A_V067")
code = code.replace("V061", "V067").replace("v061", "v067")
exec(compile(code, str(base) + "::v067", "exec"), globals(), globals())
