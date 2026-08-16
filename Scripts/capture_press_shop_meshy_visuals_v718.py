"""Capture the clean Meshy-only visible press successor using the accepted v704 cameras."""
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
source_path = root / "Scripts/capture_press_shop_complete_trains_v705.py"
code = source_path.read_text(encoding="utf-8")
code = code.replace("LB_PressShop_CompleteTrainsABCD_Cameras_v704", "LB_PressShop_MeshyPressVisuals_v717")
code = code.replace("complete_trains_abcd_v705", "meshy_press_visuals_v718")
code = code.replace("press_shop_complete_trains_visual_capture_v705", "press_shop_meshy_press_visuals_capture_v718")
code = code.replace('"revision":"v705"', '"revision":"v718"').replace("V705_", "V718_")
exec(compile(code, str(source_path), "exec"), globals(), globals())
