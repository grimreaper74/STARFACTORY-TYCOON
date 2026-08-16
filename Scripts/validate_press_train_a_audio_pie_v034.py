"""Run spatial audio cause/effect gate on collision-safe fabrication v034."""

from pathlib import Path


source = Path(__file__).with_name("validate_press_train_a_audio_pie_v026.py")
code = source.read_text(encoding="utf-8").replace("v026", "v034").replace("V026", "V034")
code = code.replace(
    "LB_PressTrainAAudioRuntimeCandidate_v034",
    "LB_PressTrainAFabricationCollisionSafeCandidate_v034",
)
code = code.replace("_v001", "_v002")
# Let the commandlet exit after the asynchronous script releases its keepalive;
# explicit editor quit can race the live audio-device reference on shutdown.
code = code.replace("    unreal.SystemLibrary.quit_editor()", "    pass")
exec(compile(code, str(source) + "::collision-safe-v034", "exec"), globals(), globals())
