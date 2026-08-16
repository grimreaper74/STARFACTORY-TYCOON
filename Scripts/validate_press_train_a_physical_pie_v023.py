"""Run the physical gameplay PIE gate against fresh v023."""

from pathlib import Path

source = Path(__file__).resolve().parent / "validate_press_train_a_physical_pie_v019.py"
code = source.read_text(encoding="utf-8").replace("v019", "v023").replace("V019", "V023")
exec(compile(code, str(source) + "::v023", "exec"), globals(), globals())
