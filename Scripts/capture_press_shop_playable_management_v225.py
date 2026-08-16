"""Capture corrected v225 through its corrected fixed cameras."""

from pathlib import Path


source = Path(__file__).with_name("capture_press_shop_playable_management_v222.py")
code = source.read_text(encoding="utf-8")
code = code.replace("v222", "v225").replace("V222", "V225")
code = code.replace("LB_WHOLE_V221_CAM_ControlRoomWalkUp", "LB_WHOLE_V224_CAM_ControlRoomWalkUp")
code = code.replace("LB_WHOLE_V219_CAM_", "LB_WHOLE_V223_CAM_")
exec(compile(code, str(source) + "::v225", "exec"), globals(), globals())

