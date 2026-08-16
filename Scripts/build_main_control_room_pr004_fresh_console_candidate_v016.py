"""Build v016 from clean v008 with a fresh post-compile PR-004 console actor."""

from pathlib import Path


SOURCE = Path(__file__).resolve().parent / "build_main_control_room_pr004_console_candidate_v009.py"
code = SOURCE.read_text(encoding="utf-8")
code = code.replace("v009", "v016")
code = code.replace("V009", "V016")
old = '''    direction = seat - screen
    horizontal = math.sqrt(direction.x * direction.x + direction.y * direction.y)
    yaw = math.degrees(math.atan2(direction.y, direction.x))
    pitch = math.degrees(math.atan2(direction.z, horizontal))
    length = math.sqrt(direction.x * direction.x + direction.y * direction.y + direction.z * direction.z)
    offset = direction * (3.0 / length)
    location = screen + offset
    rotation = unreal.Rotator(pitch, yaw, 0.0)'''
new = '''    yaw = 90.0 - 8.786
    pitch = -12.0
    pitch_rad = math.radians(pitch)
    yaw_rad = math.radians(yaw)
    normal = unreal.Vector(
        math.cos(pitch_rad) * math.cos(yaw_rad),
        math.cos(pitch_rad) * math.sin(yaw_rad),
        math.sin(pitch_rad),
    )
    offset = normal * 8.0
    location = screen + offset
    rotation = unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)'''
if old not in code:
    raise RuntimeError("v009 placement block changed; refusing unverified v016 rewrite")
code = code.replace(old, new)
marker = '''levels.save_current_level()
payload = {'''
replacement = '''# Start at the selected PR-004 screen while preserving seated look controls.
player_start = next((a for a in actors_api.get_all_level_actors() if isinstance(a, unreal.PlayerStart)), None)
if player_start is None:
    failures.append("missing inherited seated PlayerStart")
else:
    view_direction = location - seat
    view_horizontal = math.sqrt(view_direction.x * view_direction.x + view_direction.y * view_direction.y)
    view_yaw = math.degrees(math.atan2(view_direction.y, view_direction.x))
    view_pitch = math.degrees(math.atan2(view_direction.z, view_horizontal))
    player_start.set_actor_location(seat, False, False)
    player_start.set_actor_rotation(unreal.Rotator(pitch=view_pitch, yaw=view_yaw, roll=0.0), False)
    player_start.set_actor_label("LB_MCR_V016_PlayerStart_PR004Selected")

levels.save_current_level()
payload = {'''
if marker not in code:
    raise RuntimeError("v009 save marker changed; refusing unverified v016 rewrite")
code = code.replace(marker, replacement)
exec(compile(code, str(SOURCE) + "::v016", "exec"), globals(), globals())
