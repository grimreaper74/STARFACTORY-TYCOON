"""v005 adapter for corrected CCTV-side open-bay Train A presentation."""

from pathlib import Path

base = Path(__file__).with_name("import_build_press_train_a_visual_candidate_v004.py")
code = base.read_text(encoding="utf-8")
code = code.replace("Presentation_v002", "Presentation_v003")
code = code.replace("_v002", "_v003")
code = code.replace(
    'SOURCE_MAP = "/Game/LineBoss/Maps/LB_PressTrainAVisualCandidate_v003"',
    'SOURCE_MAP = "/Game/LineBoss/Maps/LB_PressTrainAOpenBayCandidate_v004"',
)
code = code.replace(
    'TARGET_MAP = "/Game/LineBoss/Maps/LB_PressTrainAOpenBayCandidate_v004"',
    'TARGET_MAP = "/Game/LineBoss/Maps/LB_PressTrainACCTVOpenBayCandidate_v005"',
)
code = code.replace("press_train_a_open_bay_build_v004.json", "press_train_a_cctv_open_bay_build_v005.json")
code = code.replace('replace("_v001", "_v003")', 'replace("_v001", "_v003").replace("_v002", "_v003")')
code = code.replace("LB.Asset.Candidate.v004", "LB.Asset.Candidate.v005")
code = code.replace("press-train-a-open-bay-build-v004", "press-train-a-cctv-open-bay-build-v005")
code = code.replace("PRESS_TRAIN_A_V004", "PRESS_TRAIN_A_V005")
code = code.replace("v004 open-bay candidate", "v005 CCTV-side open-bay candidate")
exec(compile(code, str(base) + "::v005", "exec"), globals(), globals())
