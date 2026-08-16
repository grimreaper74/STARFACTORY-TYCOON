"""Capture v709 with retained legacy aggregates disabled."""
from pathlib import Path
import unreal
root=Path(unreal.Paths.project_dir());src=root/"Scripts/capture_press_shop_complete_trains_v705.py";code=src.read_text(encoding="utf-8")
code=code.replace("LB_PressShop_CompleteTrainsABCD_Cameras_v704","LB_PressShop_NewPressVisualsOnly_v709")
code=code.replace("complete_trains_abcd_v705","new_press_visuals_v710").replace("press_shop_complete_trains_visual_capture_v705","press_shop_new_press_visuals_capture_v710")
code=code.replace('"revision":"v705"','"revision":"v710"').replace("V705_","V710_")
exec(compile(code,str(src),"exec"),globals(),globals())
