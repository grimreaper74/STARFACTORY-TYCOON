"""Audit adapter for corrected CCTV-side shared presentation source v003."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_shared_source_v001.py")
code = base.read_text(encoding="utf-8")
code = code.replace("Blockout_v001", "Presentation_v003")
code = code.replace("_v001", "_v003")
code = code.replace("source-v001", "source-v003")
code = code.replace("SHARED_V001", "SHARED_V003")
code = code.replace("SOURCE_V001", "SOURCE_V003")
exec(compile(code, str(base) + "::presentation_v003", "exec"), globals(), globals())
