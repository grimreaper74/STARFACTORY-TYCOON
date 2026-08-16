"""v044 exact-map adapter for the two-view operations evidence suite."""

from pathlib import Path

base = Path(__file__).with_name("capture_main_control_room_press_shop_operations_v043.py")
code = base.read_text(encoding="utf-8")
code = code.replace("LB_MainControlRoom_PressShopOperationsEvidenceCandidate_v043",
                    "LB_MainControlRoom_PressShopOperationsRotationCandidate_v044")
code = code.replace("LB_MCR_V043_CAPTURE", "LB_MCR_V044_CAPTURE")
code = code.replace("LB_MCR_V043_CAM_", "LB_MCR_V044_CAM_")
code = code.replace("v043_press_shop_operations", "v044_press_shop_operations")
code = code.replace("main_control_room_v043_", "main_control_room_v044_")
code = code.replace("v043 Press Shop operations", "v044 Press Shop operations")
exec(compile(code, str(base) + "::v044", "exec"), globals(), globals())
