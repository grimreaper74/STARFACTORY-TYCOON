"""v020 four-camera capture adapter, including die-change service side."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_train_a_isolated_v001.py")
code = base.read_text(encoding="utf-8")
code = code.replace("/Game/LineBoss/Maps/LB_PressTrainAIsolatedCandidate_v001", "/Game/LineBoss/Maps/LB_PressTrainAServiceCameraCandidate_v020")
code = code.replace("LB_PRESS_TRAIN_A_V001_CAPTURE", "LB_PRESS_TRAIN_A_V020_CAPTURE")
code = code.replace("Press Train A v001", "Press Train A v020")
code = code.replace("press_train_a_v001", "press_train_a_v020")
code = code.replace("PRESS_TRAIN_A_V001_CAPTURE", "PRESS_TRAIN_A_V020_CAPTURE")
code = code.replace(
    '    "draw": ("CA_MW_PTA_CAM_DrawStage", "press_train_a_v020_draw_stage.png"),',
    '    "draw": ("CA_MW_PTA_CAM_DrawStage", "press_train_a_v020_draw_stage.png"),\n    "service": ("CA_MW_PTA_CAM_DieChangeService", "press_train_a_v020_die_change_service.png"),',
)
exec(compile(code, str(base) + "::v020", "exec"), globals(), globals())
