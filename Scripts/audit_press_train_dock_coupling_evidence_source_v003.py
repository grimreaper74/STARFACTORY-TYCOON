"""Independent file/contract audit for warning-clean DockCouplingEvidence_v003."""

from pathlib import Path


base = Path(__file__).with_name("audit_press_train_dock_coupling_evidence_source_v002.py")
code = base.read_text(encoding="utf-8").replace("v002", "v003").replace("V002", "V003")
exec(compile(code, str(base) + "::v003", "exec"), globals(), globals())
