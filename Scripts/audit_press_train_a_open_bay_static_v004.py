"""v004 exact-map adapter for isolated Train A open-bay static authority."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_isolated_static_v001.py")
code = base.read_text(encoding="utf-8")
code = code.replace("/Game/LineBoss/Maps/LB_PressTrainAIsolatedCandidate_v001", "/Game/LineBoss/Maps/LB_PressTrainAOpenBayCandidate_v004")
code = code.replace("Saved/Audits/PressTrains/press_train_a_isolated_static_v001.json", "Saved/Audits/PressTrains/press_train_a_open_bay_static_v004.json")
code = code.replace("press-train-a-isolated-static-v001", "press-train-a-open-bay-static-v004")
code = code.replace("PRESS_TRAIN_A_V001", "PRESS_TRAIN_A_V004")
exec(compile(code, str(base) + "::v004", "exec"), globals(), globals())
