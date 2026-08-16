"""Capture the clean map containing only new train components."""
from pathlib import Path
import unreal
root=Path(unreal.Paths.project_dir());source_path=root/"Scripts/capture_press_shop_complete_trains_v703.py"
code=source_path.read_text(encoding="utf-8")
code=code.replace("LB_PressShop_CompleteTrainsABCD_Visual_v702","LB_PressShop_CleanMeshyTrainsReview_v723")
code=code.replace("complete_trains_abcd_v703","clean_new_trains_v724")
code=code.replace("press_shop_complete_trains_visual_capture_v703","press_shop_clean_new_trains_capture_v724")
code=code.replace('SHOTS=[("LB_V702_CAM_FourTrainSouthOverview","four_train_south_overview.png"),("LB_V702_CAM_FourTrainHighSouth","four_train_high_south.png"),("LB_V702_CAM_TrainAOperator","train_a_operator_in_shop.png")]',
'''SHOTS=[("LB_V723_CAM_EastEnd","clean_trains_east_end.png"),("LB_V723_CAM_EastHigh","clean_trains_east_high.png"),("LB_V723_CAM_SouthEast","clean_trains_south_east.png")]''')
code=code.replace('"revision":"v703"','"revision":"v724"').replace("V703_","V724_")
exec(compile(code,str(source_path),"exec"),globals(),globals())
