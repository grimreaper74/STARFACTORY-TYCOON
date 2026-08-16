"""Run the exact-map static gate on isolated Train A v057."""

from pathlib import Path


base = Path(__file__).with_name("audit_press_train_a_dock_coupling_static_v056.py")
code = base.read_text(encoding="utf-8")
code = code.replace("Candidate_v056", "Candidate_v057")
code = code.replace("static_v056", "static_v057")
code = code.replace("static-v056", "static-v057")
code = code.replace("LB.Asset.Candidate.v056", "LB.Asset.Candidate.v057")
code = code.replace("PRESS_TRAIN_A_V056", "PRESS_TRAIN_A_V057")
code = code.replace("V056", "V057").replace("v056", "v057")
exec(compile(code, str(base) + "::v057", "exec"), globals(), globals())
