"""Run the navigation-aware static gate against fresh v023."""

from pathlib import Path

source = Path(__file__).resolve().parent / "audit_press_train_a_physical_static_v020.py"
code = source.read_text(encoding="utf-8").replace("v020", "v023").replace("V020", "V023")
exec(compile(code, str(source) + "::v023", "exec"), globals(), globals())
