"""Run the proven Train A audio cause/effect gate on v027 and v002 assets."""

from pathlib import Path

source = Path(__file__).resolve().parent / "validate_press_train_a_audio_pie_v026.py"
code = source.read_text(encoding="utf-8").replace("v026", "v027").replace("V026", "V027")
code = code.replace("_v001", "_v002")
exec(compile(code, str(source) + "::v027", "exec"), globals(), globals())
