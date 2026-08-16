"""v003 exact-map adapter for the control-room fixed camera suite."""

from pathlib import Path

base = Path(__file__).with_name("capture_main_control_room_candidate_v001.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_MainControlRoom_IntegrationCandidate_v001", "LB_MainControlRoom_SeatedVisualCandidate_v003")
code = code.replace("LB_MCR_V001_CAPTURE", "LB_MCR_V003_CAPTURE")
code = code.replace("LB_MCR_V001_CAM_", "LB_MCR_V003_CAM_")
code = code.replace("v001_integration", "v003_seated_visual")
code = code.replace("main_control_room_v001_", "main_control_room_v003_")
code = code.replace("control room v001 integration", "control room v003 seated visual")
exec(compile(code, str(base) + "::v003", "exec"), globals(), globals())

