"""Run the physical gameplay PIE gate against fresh v024."""

from pathlib import Path

source = Path(__file__).resolve().parent / "validate_press_train_a_physical_pie_v019.py"
code = source.read_text(encoding="utf-8").replace("v019", "v024").replace("V019", "V024")
exec(compile(code, str(source) + "::v024", "exec"), globals(), globals())
