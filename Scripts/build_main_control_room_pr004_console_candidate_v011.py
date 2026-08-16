"""Build v011 from clean v008 with corrected Unreal Rotator field mapping."""

from pathlib import Path


SOURCE = Path(__file__).resolve().parent / "build_main_control_room_pr004_console_candidate_v009.py"
code = SOURCE.read_text(encoding="utf-8")
code = code.replace("v009", "v011")
code = code.replace("V009", "V011")
code = code.replace(
    "rotation = unreal.Rotator(pitch, yaw, 0.0)",
    "rotation = unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)",
)
exec(compile(code, str(SOURCE) + "::v011", "exec"), globals(), globals())
