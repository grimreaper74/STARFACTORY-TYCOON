"""v021 four-camera capture adapter including corrected service evidence."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_isolated_v001.py")
code = base.read_text(encoding="utf-8")
code = code.replace("/Game/LineBoss/Maps/LB_PressTrainAIsolatedCandidate_v001", "/Game/LineBoss/Maps/LB_PressTrainAServiceEvidenceCandidate_v021")
code = code.replace("LB_PRESS_TRAIN_A_V001_CAPTURE", "LB_PRESS_TRAIN_A_V021_CAPTURE")
code = code.replace("Press Train A v001", "Press Train A v021")
code = code.replace("press_train_a_v001", "press_train_a_v021")
code = code.replace("PRESS_TRAIN_A_V001_CAPTURE", "PRESS_TRAIN_A_V021_CAPTURE")
code = code.replace(
    '    "draw": ("CA_MW_PTA_CAM_DrawStage", "press_train_a_v021_draw_stage.png"),',
    '    "draw": ("CA_MW_PTA_CAM_DrawStage", "press_train_a_v021_draw_stage.png"),\n    "service": ("CA_MW_PTA_CAM_DieChangeService", "press_train_a_v021_die_change_service.png"),',
)
exec(compile(code, str(base) + "::v021", "exec"), globals(), globals())
