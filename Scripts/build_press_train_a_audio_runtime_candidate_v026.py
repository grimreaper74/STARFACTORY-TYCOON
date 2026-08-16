"""Fresh v026 direct from v024 with the UE 5.8 component-location accessor."""

from pathlib import Path

source = Path(__file__).resolve().parent / "build_press_train_a_audio_runtime_candidate_v025.py"
code = source.read_text(encoding="utf-8").replace("v025", "v026").replace("V025", "V026")
code = code.replace('component.get_relative_location().x', 'component.get_editor_property("relative_location").x')
code = code.replace('component.get_relative_location().y', 'component.get_editor_property("relative_location").y')
code = code.replace('component.get_relative_location().z', 'component.get_editor_property("relative_location").z')
exec(compile(code, str(source) + "::v026", "exec"), globals(), globals())
