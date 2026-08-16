"""Run the physical gameplay PIE gate against fresh v022."""

from pathlib import Path

source = Path(__file__).resolve().parent / "validate_press_train_a_physical_pie_v019.py"
code = source.read_text(encoding="utf-8").replace("v019", "v022").replace("V019", "V022")
exec(compile(code, str(source) + "::v022", "exec"), globals(), globals())
