"""Run the proven motion/safety/save gate against one isolated Train B-D variant."""

import os
from pathlib import Path

letter = os.environ.get("LB_PT_VARIANT", "").upper()
if letter not in {"B", "C", "D"}:
    raise RuntimeError("LB_PT_VARIANT must be B, C or D")
source = Path(__file__).resolve().parent / "validate_press_train_a_motion_pie_v012.py"
code = source.read_text(encoding="utf-8")
code = code.replace("MW.MCR.TRAIN_A.CONSOLE", f"MW.MCR.TRAIN_{letter}.CONSOLE")
code = code.replace("TRAIN A", f"TRAIN {letter}")
code = code.replace("PTA-", f"PT{letter}-")
exec(compile(code, str(source) + f"::train-{letter}-variant-v001", "exec"), globals(), globals())
