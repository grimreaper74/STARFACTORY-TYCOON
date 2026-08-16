"""Capture one fixed view from an isolated Train B-D v001 variant."""

import os
from pathlib import Path

letter = os.environ.get("LB_PT_VARIANT", "").upper()
if letter not in {"B", "C", "D"}:
    raise RuntimeError("LB_PT_VARIANT must be B, C or D")
source = Path(__file__).resolve().parent / "capture_press_train_a_isolated_v001.py"
code = source.read_text(encoding="utf-8")
code = code.replace(
    "/Game/LineBoss/Maps/LB_PressTrainAIsolatedCandidate_v001",
    f"/Game/LineBoss/Maps/LB_PressTrain{letter}IsolatedVariantCandidate_v001")
code = code.replace("press_train_a_v001", f"press_train_{letter.lower()}_variant_v001")
code = code.replace("Press Train A v001", f"Press Train {letter} isolated variant v001")
code = code.replace("PRESS_TRAIN_A_V001_CAPTURE", f"PRESS_TRAIN_{letter}_VARIANT_V001_CAPTURE")
# The v001 capture harness predates the fixed-camera v009 set retained by the
# v027 lineage.  Keep its stable capture IDs while resolving them to the actual
# retained camera actors present in every isolated B-D successor.
code = code.replace("CA_MW_PTA_CAM_Hero\"", "CA_MW_PTA_CAM_Hero_v009\"")
code = code.replace("CA_MW_PTA_CAM_Overview\"", "CA_MW_PTA_CAM_Overhead_v009\"")
code = code.replace("CA_MW_PTA_CAM_DrawStage\"", "CA_MW_PTA_CAM_S07_v009\"")
exec(compile(code, str(source) + f"::train-{letter}-variant-v001", "exec"), globals(), globals())
