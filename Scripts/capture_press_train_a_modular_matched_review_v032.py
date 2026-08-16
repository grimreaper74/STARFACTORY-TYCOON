"""Run the established bright matched review against axis-corrected v032."""
from pathlib import Path
base=Path(__file__).with_name("capture_press_train_a_modular_matched_review_v031.py")
code=base.read_text(encoding="utf-8").replace("ModularAssembly_v031","ModularAssembly_v032").replace("MATCHED_REVIEW_v031","MATCHED_REVIEW_v032").replace("_v031","_v032").replace("-v031","-v032")
exec(compile(code,str(base)+"::v032","exec"),globals(),globals())
