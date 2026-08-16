"""Build isolated Train A v068 directly from v053 with coupling v003."""

from pathlib import Path


base = Path(__file__).with_name("import_build_press_train_a_dock_coupling_candidate_v061.py")
code = base.read_text(encoding="utf-8")
code = code.replace("Candidate_v061", "Candidate_v068")
code = code.replace("evidence_v061", "evidence_v068")
code = code.replace("candidate-v061", "candidate-v068")
code = code.replace("LB.Asset.Candidate.v061", "LB.Asset.Candidate.v068")
code = code.replace("PRESS_TRAIN_A_V061", "PRESS_TRAIN_A_V068")
code = code.replace("V061", "V068").replace("v061", "v068")
exec(compile(code, str(base) + "::v068", "exec"), globals(), globals())
