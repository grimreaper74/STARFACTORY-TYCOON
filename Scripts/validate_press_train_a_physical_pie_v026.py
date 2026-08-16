"""Run the exact retained-v024 physical gate on the audio-only v026 child."""

from pathlib import Path

source = Path(__file__).resolve().parent / "validate_press_train_a_physical_pie_v024.py"
adapter = source.read_text(encoding="utf-8")
needle = 'exec(compile(code, str(source) + "::v024", "exec"), globals(), globals())'
replacement = '''code = code.replace(
    "/Game/LineBoss/Maps/LB_PressTrainAPhysicalGameplayCandidate_v024",
    "/Game/LineBoss/Maps/LB_PressTrainAAudioRuntimeCandidate_v026")
code = code.replace(
    "Saved/Audits/PressTrains/press_train_a_physical_pie_v024.json",
    "Saved/Audits/PressTrains/press_train_a_physical_pie_v026.json")
exec(compile(code, str(source) + "::audio-v026-on-physical-v024", "exec"), globals(), globals())'''
if needle not in adapter:
    raise RuntimeError("v024 physical adapter changed; refusing v026 wrapper")
adapter = adapter.replace(needle, replacement, 1)
exec(compile(adapter, str(source) + "::v026-wrapper", "exec"), globals(), globals())
