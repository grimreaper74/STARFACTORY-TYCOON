"""v006 exact-map adapter for the control-room fixed camera suite."""

from pathlib import Path

base = Path(__file__).with_name("capture_main_control_room_candidate_v001.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_MainControlRoom_IntegrationCandidate_v001", "LB_MainControlRoom_MonitorPitchCandidate_v006")
code = code.replace("LB_MCR_V001_CAPTURE", "LB_MCR_V006_CAPTURE")
code = code.replace("LB_MCR_V001_CAM_", "LB_MCR_V006_CAM_")
code = code.replace("v001_integration", "v006_monitor_pitch")
code = code.replace("main_control_room_v001_", "main_control_room_v006_")
code = code.replace("control room v001 integration", "control room v006 monitor pitch")
exec(compile(code, str(base) + "::v006", "exec"), globals(), globals())

