"""Fresh direct-v386 placement of normal-corrected physical signs v410/v411."""
from pathlib import Path
source=Path(__file__).with_name("build_press_shop_physical_train_identity_candidate_v400.py")
code=source.read_text(encoding="utf-8").replace("PhysicalSigns_v397","PhysicalSigns_v411").replace("_v396","_v410").replace("v400","v412").replace("yaw=180.0","yaw=0.0").replace('"rotation_yaw":180.0','"rotation_yaw":0.0').replace("V398_BACKFACE_AND_MATERIAL_FAILURES_CORRECTED","V398_V400_V404_V408_FAILURES_CORRECTED_WITH_READABLE_NORMAL_CORRECT_PHYSICAL_MESH")
exec(compile(code,str(source),"exec"),{"__name__":"__main__","__file__":str(source)})
