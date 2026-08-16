"""Build v013 with the live HMI flush to the authored physical panel plane."""

from pathlib import Path


SOURCE = Path(__file__).resolve().parent / "build_main_control_room_pr004_console_candidate_v009.py"
code = SOURCE.read_text(encoding="utf-8")
code = code.replace("v009", "v013")
code = code.replace("V009", "V013")
old = '''    direction = seat - screen
    horizontal = math.sqrt(direction.x * direction.x + direction.y * direction.y)
    yaw = math.degrees(math.atan2(direction.y, direction.x))
    pitch = math.degrees(math.atan2(direction.z, horizontal))
    length = math.sqrt(direction.x * direction.x + direction.y * direction.y + direction.z * direction.z)
    offset = direction * (3.0 / length)
    location = screen + offset
    rotation = unreal.Rotator(pitch, yaw, 0.0)'''
new = '''    # The physical panel is rotated +8.786 degrees in Blender about Z.
    # After Blender-to-Unreal conversion its +Y face becomes an Unreal +X
    # WidgetComponent normal at yaw 90-8.786. Keep the same -12 degree pitch.
    yaw = 90.0 - 8.786
    pitch = -12.0
    pitch_rad = math.radians(pitch)
    yaw_rad = math.radians(yaw)
    normal = unreal.Vector(
        math.cos(pitch_rad) * math.cos(yaw_rad),
        math.cos(pitch_rad) * math.sin(yaw_rad),
        math.sin(pitch_rad),
    )
    offset = normal * 3.0
    location = screen + offset
    rotation = unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)'''
if old not in code:
    raise RuntimeError("v009 placement block changed; refusing an unverified transform rewrite")
code = code.replace(old, new)
exec(compile(code, str(SOURCE) + "::v013", "exec"), globals(), globals())
