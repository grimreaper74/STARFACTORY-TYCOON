"""Build isolated Train A v061 directly from v053 with coupling v003."""

from pathlib import Path


base = Path(__file__).with_name("import_build_press_train_a_dock_coupling_candidate_v060.py")
code = base.read_text(encoding="utf-8")
code = code.replace("Candidate_v060", "Candidate_v061")
code = code.replace("evidence_v060", "evidence_v061")
code = code.replace("candidate-v060", "candidate-v061")
code = code.replace("LB.Asset.Candidate.v060", "LB.Asset.Candidate.v061")
code = code.replace("PRESS_TRAIN_A_V060", "PRESS_TRAIN_A_V061")
code = code.replace("V060", "V061").replace("v060", "v061")
exec(compile(code, str(base) + "::v061", "exec"), globals(), globals())
