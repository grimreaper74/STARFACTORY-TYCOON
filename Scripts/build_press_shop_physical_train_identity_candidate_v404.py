"""Fresh direct-v386 v404 using v402 outward lettering at audited yaw zero."""
from pathlib import Path

source=Path(__file__).with_name("build_press_shop_physical_train_identity_candidate_v400.py")
code=source.read_text(encoding="utf-8")
code=code.replace("PhysicalSigns_v397","PhysicalSigns_v403")
code=code.replace("_v396","_v402")
code=code.replace("v400","v404")
code=code.replace("yaw=180.0","yaw=0.0")
code=code.replace('"rotation_yaw":180.0','"rotation_yaw":0.0')
code=code.replace("V398_BACKFACE_AND_MATERIAL_FAILURES_CORRECTED","V398_V400_VISUAL_FAILURES_CORRECTED_WITH_OUTWARD_MESH_LETTERING")
exec(compile(code,str(source),"exec"),{"__name__":"__main__","__file__":str(source)})
