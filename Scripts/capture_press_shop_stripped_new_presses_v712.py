"""Capture v711 after removing block shells and old combined backgrounds."""
from pathlib import Path
import unreal
root=Path(unreal.Paths.project_dir());src=root/"Scripts/capture_press_shop_complete_trains_v705.py";code=src.read_text(encoding="utf-8")
code=code.replace("LB_PressShop_CompleteTrainsABCD_Cameras_v704","LB_PressShop_StrippedNewPresses_v711")
code=code.replace("complete_trains_abcd_v705","stripped_new_presses_v712").replace("press_shop_complete_trains_visual_capture_v705","press_shop_stripped_new_presses_capture_v712")
code=code.replace('"revision":"v705"','"revision":"v712"').replace("V705_","V712_")
exec(compile(code,str(src),"exec"),globals(),globals())
