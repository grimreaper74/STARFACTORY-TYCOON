"""Run the exact navigation-aware static gate against fresh v022."""

from pathlib import Path

source = Path(__file__).resolve().parent / "audit_press_train_a_physical_static_v020.py"
code = source.read_text(encoding="utf-8").replace("v020", "v022").replace("V020", "V022")
exec(compile(code, str(source) + "::v022", "exec"), globals(), globals())
