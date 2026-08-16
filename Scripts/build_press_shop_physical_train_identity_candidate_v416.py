"""Fresh direct-v386 sign candidate with two-sided lettering material only."""
from pathlib import Path
source=Path(__file__).with_name("build_press_shop_physical_train_identity_candidate_v400.py")
code=source.read_text(encoding="utf-8")
code=code.replace("PhysicalSigns_v397","PhysicalSigns_v411").replace("_v396","_v410").replace("v400","v416").replace("yaw=180.0","yaw=0.0").replace('"rotation_yaw":180.0','"rotation_yaw":0.0')
code=code.replace('lib.load_asset(MATROOT+"/M_CA_MW_PR009_LabelWhite_v086")','lib.load_asset("/Game/LineBoss/Candidates/PressShop/TrainIdentity/ReleaseMaterials_v414/M_CA_MW_IdentityLetterWhite_TwoSided_v414")')
code=code.replace("V398_BACKFACE_AND_MATERIAL_FAILURES_CORRECTED","V398_V400_V404_V408_V412_FAILURES_CORRECTED_WITH_TWO_SIDED_LETTER_SLOT")
exec(compile(code,str(source),"exec"),{"__name__":"__main__","__file__":str(source)})
