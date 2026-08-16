"""Run the exact-map static gate on isolated Train A v060.

The v060 candidate uses the warning-clean, low-profile v003 dock coupling.
"""

from pathlib import Path


base = Path(__file__).with_name("audit_press_train_a_dock_coupling_static_v056.py")
code = base.read_text(encoding="utf-8")
code = code.replace("Candidate_v056", "Candidate_v060")
code = code.replace("static_v056", "static_v060")
code = code.replace("static-v056", "static-v060")
code = code.replace("LB.Asset.Candidate.v056", "LB.Asset.Candidate.v060")
code = code.replace("PRESS_TRAIN_A_V056", "PRESS_TRAIN_A_V060")
code = code.replace("DockCouplingEvidence_v001", "DockCouplingEvidence_v003")
code = code.replace("DockCouplingEngaged_v001", "DockCouplingEngaged_v003")
code = code.replace("V056", "V060").replace("v056", "v060")
exec(compile(code, str(base) + "::v060", "exec"), globals(), globals())
