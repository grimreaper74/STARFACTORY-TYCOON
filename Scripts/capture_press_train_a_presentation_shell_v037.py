from pathlib import Path
src=Path(__file__).with_name("capture_press_train_a_fabrication_v034.py")
code=src.read_text(encoding="utf-8").replace("v034","v037").replace("V034","V037").replace("fabrication","presentation_shell")
code=code.replace("LB_PressTrainAFabricationCollisionSafeCandidate_v037","LB_PressTrainAPresentationShellCandidate_v037")
exec(compile(code,str(src)+"::presentation-shell-v037","exec"),{"__name__":"__main__","__file__":str(src).replace("v034","v037")})
