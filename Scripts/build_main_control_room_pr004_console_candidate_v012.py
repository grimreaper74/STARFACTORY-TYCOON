"""Build v012 using the WidgetComponent front-face (-X) orientation."""

from pathlib import Path


SOURCE = Path(__file__).resolve().parent / "build_main_control_room_pr004_console_candidate_v009.py"
code = SOURCE.read_text(encoding="utf-8")
code = code.replace("v009", "v012")
code = code.replace("V009", "V012")
code = code.replace(
    "rotation = unreal.Rotator(pitch, yaw, 0.0)",
    "rotation = unreal.Rotator(pitch=-pitch, yaw=yaw + 180.0, roll=0.0)",
)
exec(compile(code, str(SOURCE) + "::v012", "exec"), globals(), globals())
