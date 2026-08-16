"""v002 exact-map adapter for corrected isolated Press Train A static authority."""

from pathlib import Path

base = Path(__file__).with_name("audit_press_train_a_isolated_static_v001.py")
code = base.read_text(encoding="utf-8")
code = code.replace("/Game/LineBoss/Maps/LB_PressTrainAIsolatedCandidate_v001", "/Game/LineBoss/Maps/LB_PressTrainAFlowAxisCandidate_v002")
code = code.replace("Saved/Audits/PressTrains/press_train_a_isolated_static_v001.json", "Saved/Audits/PressTrains/press_train_a_flow_axis_static_v002.json")
code = code.replace("press-train-a-isolated-static-v001", "press-train-a-flow-axis-static-v002")
code = code.replace("PRESS_TRAIN_A_V001", "PRESS_TRAIN_A_V002")
exec(compile(code, str(base) + "::v002", "exec"), globals(), globals())
