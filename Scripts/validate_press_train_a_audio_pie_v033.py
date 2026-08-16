"""Run the retained spatial audio cause/effect gate on fabrication v033."""

from pathlib import Path


source = Path(__file__).with_name("validate_press_train_a_audio_pie_v026.py")
code = source.read_text(encoding="utf-8").replace("v026", "v033").replace("V026", "V033")
code = code.replace(
    "LB_PressTrainAAudioRuntimeCandidate_v033",
    "LB_PressTrainAFabricationCandidate_v033",
)
code = code.replace("_v001", "_v002")
exec(compile(code, str(source) + "::fabrication-v033", "exec"), globals(), globals())
