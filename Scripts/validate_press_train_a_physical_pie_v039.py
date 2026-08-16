from pathlib import Path
source=Path(__file__).with_name("validate_press_train_a_physical_pie_v033.py")
code=source.read_text(encoding="utf-8").replace("v033","v039").replace("V033","V039")
code=code.replace("LB_PressTrainAFabricationCandidate_v039","LB_PressTrainAPresentationShellMaterialCandidate_v039")
exec(compile(code,str(source)+"::presentation-shell-v039","exec"),globals(),globals())
