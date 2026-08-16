"""Fresh v027 direct from retained v024, using the distortion-free v002 audio set."""

from pathlib import Path

source = Path(__file__).resolve().parent / "build_press_train_a_audio_runtime_candidate_v025.py"
code = source.read_text(encoding="utf-8").replace("v025", "v027").replace("V025", "V027")
code = code.replace("Candidate_v001", "Candidate_v002").replace("_v001", "_v002")
code = code.replace('component.get_relative_location().x', 'component.get_editor_property("relative_location").x')
code = code.replace('component.get_relative_location().y', 'component.get_editor_property("relative_location").y')
code = code.replace('component.get_relative_location().z', 'component.get_editor_property("relative_location").z')
exec(compile(code, str(source) + "::v027", "exec"), globals(), globals())
