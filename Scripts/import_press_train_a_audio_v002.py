"""Import isolated Train A audio Candidate_v002 from the v002 source set."""

from pathlib import Path

source = Path(__file__).resolve().parent / "import_press_train_a_audio_v001.py"
code = source.read_text(encoding="utf-8").replace("v001", "v002").replace("V001", "V002")
exec(compile(code, str(source) + "::v002", "exec"), globals(), globals())
