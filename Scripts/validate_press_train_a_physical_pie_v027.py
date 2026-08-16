"""Run the retained-v024 physical gate on the audio-only v027 child."""

from pathlib import Path

source = Path(__file__).resolve().parent / "validate_press_train_a_physical_pie_v026.py"
code = source.read_text(encoding="utf-8").replace("v026", "v027").replace("V026", "V027")
exec(compile(code, str(source) + "::v027", "exec"), globals(), globals())
