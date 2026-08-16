"""Build isolated Train A v066 directly from v053 with coupling v003."""

from pathlib import Path


base = Path(__file__).with_name("import_build_press_train_a_dock_coupling_candidate_v061.py")
code = base.read_text(encoding="utf-8")
code = code.replace("Candidate_v061", "Candidate_v066")
code = code.replace("evidence_v061", "evidence_v066")
code = code.replace("candidate-v061", "candidate-v066")
code = code.replace("LB.Asset.Candidate.v061", "LB.Asset.Candidate.v066")
code = code.replace("PRESS_TRAIN_A_V061", "PRESS_TRAIN_A_V066")
code = code.replace("V061", "V066").replace("v061", "v066")
exec(compile(code, str(base) + "::v066", "exec"), globals(), globals())
