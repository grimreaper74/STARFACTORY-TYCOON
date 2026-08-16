"""Run the exact-map static gate on isolated Train A v058."""

from pathlib import Path


base = Path(__file__).with_name("audit_press_train_a_dock_coupling_static_v057.py")
code = base.read_text(encoding="utf-8")
code = code.replace("Candidate_v057", "Candidate_v058")
code = code.replace("static_v057", "reference_finish_static_v058")
code = code.replace("static-v057", "reference-finish-static-v058")
code = code.replace("LB.Asset.Candidate.v057", "LB.Asset.Candidate.v058")
code = code.replace("PRESS_TRAIN_A_V057", "PRESS_TRAIN_A_V058")
code = code.replace("V057", "V058").replace("v057", "v058")
exec(compile(code, str(base) + "::v058", "exec"), globals(), globals())
