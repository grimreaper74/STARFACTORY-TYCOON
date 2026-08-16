"""Run physical control-room button routing on exact v288 without overwriting retained evidence."""
from pathlib import Path

source = Path(__file__).with_name("validate_control_room_physical_buttons_pie_v228.py")
code = source.read_text(encoding="utf-8").replace("v228", "v288").replace("V228", "V288")
code = code.replace(
    "Saved/Audits/ControlRoom/control_room_physical_buttons_pie_v288.json",
    "Saved/Audits/ControlRoom/control_room_physical_buttons_pie_v288_orchestration_v001.json")
exec(compile(code, str(source) + "::v288-orchestration-v001", "exec"), globals(), globals())
