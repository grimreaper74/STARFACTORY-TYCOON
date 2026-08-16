"""Audit adapter for the open-bay shared press-train presentation source v002."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_shared_source_v001.py")
code = base.read_text(encoding="utf-8")
code = code.replace("Blockout_v001", "Presentation_v002")
code = code.replace("_v001", "_v002")
code = code.replace("source-v001", "source-v002")
code = code.replace("SHARED_V001", "SHARED_V002")
code = code.replace("SOURCE_V001", "SOURCE_V002")
exec(compile(code, str(base) + "::presentation_v002", "exec"), globals(), globals())
