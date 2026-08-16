from pathlib import Path
source=Path(__file__).with_name("validate_press_train_a_audio_pie_v026.py")
code=source.read_text(encoding="utf-8").replace("v026","v039").replace("V026","V039")
code=code.replace("LB_PressTrainAAudioRuntimeCandidate_v039","LB_PressTrainAPresentationShellMaterialCandidate_v039").replace("_v001","_v002")
code=code.replace("    unreal.SystemLibrary.quit_editor()","    pass")
exec(compile(code,str(source)+"::presentation-shell-v039","exec"),globals(),globals())
