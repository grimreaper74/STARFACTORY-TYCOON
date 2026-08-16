"""Run the exact v020 static gate against fresh v021."""

from pathlib import Path

source = Path(__file__).resolve().parent / "audit_press_train_a_physical_static_v020.py"
code = source.read_text(encoding="utf-8").replace("v020", "v021").replace("V020", "V021")
exec(compile(code, str(source) + "::v021", "exec"), globals(), globals())
