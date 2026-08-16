"""Build isolated Train A v063 directly from v053 with coupling v003."""

from pathlib import Path


base = Path(__file__).with_name("import_build_press_train_a_dock_coupling_candidate_v061.py")
code = base.read_text(encoding="utf-8")
code = code.replace("Candidate_v061", "Candidate_v063")
code = code.replace("evidence_v061", "evidence_v063")
code = code.replace("candidate-v061", "candidate-v063")
code = code.replace("LB.Asset.Candidate.v061", "LB.Asset.Candidate.v063")
code = code.replace("PRESS_TRAIN_A_V061", "PRESS_TRAIN_A_V063")
code = code.replace("V061", "V063").replace("v061", "v063")
exec(compile(code, str(base) + "::v063", "exec"), globals(), globals())
