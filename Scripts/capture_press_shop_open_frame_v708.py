"""Capture v707 housing-hidden experiment using accepted inside-hall cameras."""
from pathlib import Path
import unreal
root=Path(unreal.Paths.project_dir());src=root/"Scripts/capture_press_shop_complete_trains_v705.py";code=src.read_text(encoding="utf-8")
code=code.replace("LB_PressShop_CompleteTrainsABCD_Cameras_v704","LB_PressShop_OpenFramePresses_v707")
code=code.replace("complete_trains_abcd_v705","open_frame_presses_v708").replace("press_shop_complete_trains_visual_capture_v705","press_shop_open_frame_visual_capture_v708")
code=code.replace('"revision":"v705"','"revision":"v708"').replace("V705_","V708_")
exec(compile(code,str(src),"exec"),globals(),globals())
