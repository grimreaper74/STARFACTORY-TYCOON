"""Run the authored controller reach audit against ergonomic child v228."""

from pathlib import Path


source = Path(__file__).with_name("audit_control_room_gamepad_reach_v226.py")
code = source.read_text(encoding="utf-8").replace("v226", "v228").replace("V226", "V228")
exec(compile(code, str(source) + "::v228", "exec"), globals(), globals())
