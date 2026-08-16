"""Run the v019 physical PIE proof against fresh navigation-enabled v020."""

from pathlib import Path

source = Path(__file__).resolve().parent / "validate_press_train_a_physical_pie_v019.py"
code = source.read_text(encoding="utf-8").replace("v019", "v020").replace("V019", "V020")
exec(compile(code, str(source) + "::v020", "exec"), globals(), globals())
