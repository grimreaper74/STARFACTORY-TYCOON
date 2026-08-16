"""Run the standing-player, clearance and navigation PIE gate against v021."""

from pathlib import Path

source = Path(__file__).resolve().parent / "validate_press_train_a_physical_pie_v019.py"
code = source.read_text(encoding="utf-8").replace("v019", "v021").replace("V019", "V021")
exec(compile(code, str(source) + "::v021", "exec"), globals(), globals())
