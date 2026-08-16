"""Build isolated Train A v060 from v053 with warning-clean coupling v003."""

from pathlib import Path


base = Path(__file__).with_name("import_build_press_train_a_dock_coupling_candidate_v059.py")
code = base.read_text(encoding="utf-8")
code = code.replace("Candidate_v059", "Candidate_v060")
code = code.replace("evidence_v059", "evidence_v060")
code = code.replace("candidate-v059", "candidate-v060")
code = code.replace("LB.Asset.Candidate.v059", "LB.Asset.Candidate.v060")
code = code.replace("PRESS_TRAIN_A_V059", "PRESS_TRAIN_A_V060")
code = code.replace("DockCouplingEvidence_v002", "DockCouplingEvidence_v003")
code = code.replace("MANIFEST_v002", "MANIFEST_v003")
code = code.replace("source_audit_v002", "source_audit_v003")
code = code.replace("DockCouplingEngaged_v002", "DockCouplingEngaged_v003")
code = code.replace("V059", "V060").replace("v059", "v060")
exec(compile(code, str(base) + "::v060", "exec"), globals(), globals())
