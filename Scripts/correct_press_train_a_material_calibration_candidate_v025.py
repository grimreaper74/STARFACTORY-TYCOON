"""Create v025 from v024 with subtle industrial material variation."""

from pathlib import Path

base = Path(__file__).with_name("correct_press_train_a_release_presentation_candidate_v024.py")
code = base.read_text(encoding="utf-8")
code = code.replace(
    'SOURCE = "/Game/LineBoss/Maps/LB_PressTrainAReleaseDetailCandidate_v023"',
    'SOURCE = "/Game/LineBoss/Maps/LB_PressTrainAReleasePresentationCandidate_v024"')
code = code.replace(
    'TARGET = "/Game/LineBoss/Maps/LB_PressTrainAReleasePresentationCandidate_v024"',
    'TARGET = "/Game/LineBoss/Maps/LB_PressTrainAMaterialCalibrationCandidate_v025"')
code = code.replace("Materials_v024", "Materials_v025")
code = code.replace("press_train_a_release_presentation_v024.json", "press_train_a_material_calibration_v025.json")
code = code.replace("M_CA_MW_PT_FoundryCharcoalLayered_v024", "M_CA_MW_PT_FoundryCharcoalLayered_v025")
code = code.replace("M_CA_MW_PT_CairnwellGreenLayered_v024", "M_CA_MW_PT_CairnwellGreenLayered_v025")
code = code.replace("M_CA_MW_PT_SafetyYellowLayered_v024", "M_CA_MW_PT_SafetyYellowLayered_v025")
code = code.replace("M_CA_MW_PT_ServiceGreyLayered_v024", "M_CA_MW_PT_ServiceGreyLayered_v025")
code = code.replace("M_CA_MW_PT_WorkedSteelLayered_v024", "M_CA_MW_PT_WorkedSteelLayered_v025")
code = code.replace("M_CA_MW_PT_TrainAAccentLayered_v024", "M_CA_MW_PT_TrainAAccentLayered_v025")
code = code.replace("M_CA_MW_PT_DarkRubberLayered_v024", "M_CA_MW_PT_DarkRubberLayered_v025")
code = code.replace("M_CA_MW_PT_LabelWhiteLayered_v024", "M_CA_MW_PT_LabelWhiteLayered_v025")
code = code.replace("M_CA_MW_PT_StateGreenRestrained_v024", "M_CA_MW_PT_StateGreenRestrained_v025")
code = code.replace("M_CA_MW_PT_StateAmberRestrained_v024", "M_CA_MW_PT_StateAmberRestrained_v025")
code = code.replace("M_CA_MW_PT_StateRedRestrained_v024", "M_CA_MW_PT_StateRedRestrained_v025")
code = code.replace("M_CA_MW_PT_StateBlueRestrained_v024", "M_CA_MW_PT_StateBlueRestrained_v025")
code = code.replace(
    '"output_min": 0.12, "output_max": 0.88, "turbulence": True,',
    '"output_min": 0.32, "output_max": 0.68, "turbulence": True,')
replacements = {
    '(0.018, 0.024, 0.026), (0.046, 0.054, 0.056), 0.48, 0.46, 0.67, 0.010':
        '(0.012, 0.016, 0.018), (0.024, 0.029, 0.031), 0.48, 0.50, 0.64, 0.075',
    '(0.012, 0.055, 0.038), (0.025, 0.125, 0.085), 0.28, 0.43, 0.62, 0.009':
        '(0.012, 0.050, 0.035), (0.022, 0.082, 0.058), 0.28, 0.48, 0.60, 0.070',
    '(0.30, 0.105, 0.002), (0.62, 0.285, 0.008), 0.20, 0.42, 0.62, 0.013':
        '(0.28, 0.100, 0.002), (0.47, 0.205, 0.006), 0.20, 0.48, 0.60, 0.085',
    '(0.075, 0.090, 0.094), (0.145, 0.165, 0.170), 0.40, 0.45, 0.64, 0.008':
        '(0.060, 0.071, 0.074), (0.095, 0.108, 0.112), 0.40, 0.50, 0.62, 0.065',
    '(0.12, 0.135, 0.145), (0.27, 0.295, 0.305), 0.90, 0.30, 0.48, 0.015':
        '(0.10, 0.115, 0.122), (0.18, 0.195, 0.205), 0.90, 0.32, 0.45, 0.090',
    '(0.010, 0.055, 0.105), (0.025, 0.150, 0.310), 0.27, 0.40, 0.58, 0.010':
        '(0.009, 0.048, 0.092), (0.018, 0.090, 0.180), 0.27, 0.46, 0.57, 0.075',
    '(0.005, 0.007, 0.008), (0.018, 0.022, 0.023), 0.02, 0.76, 0.90, 0.020':
        '(0.004, 0.006, 0.007), (0.011, 0.014, 0.015), 0.02, 0.80, 0.90, 0.110',
    '(0.30, 0.35, 0.34), (0.58, 0.64, 0.62), 0.14, 0.36, 0.52, 0.015':
        '(0.24, 0.28, 0.27), (0.42, 0.47, 0.45), 0.14, 0.40, 0.50, 0.100',
}
for old, new in replacements.items():
    if old not in code:
        raise RuntimeError(f"material calibration source token missing: {old}")
    code = code.replace(old, new)
code = code.replace(
    'bias = 0.78 if actor.get_actor_label() == "CA_MW_PTA_CAM_DieChangeService" else 0.88',
    'bias = 0.60 if actor.get_actor_label() == "CA_MW_PTA_CAM_DieChangeService" else 0.64')
code = code.replace("if len(removed_text) != 12:", "if len(removed_text) != 0:")
code = code.replace("expected 12 temporary release-detail text actors removed", "expected zero temporary release-detail text actors in v024 source")
code = code.replace("LB.Asset.Candidate.v024", "LB.Asset.Candidate.v025")
code = code.replace("PRESS_TRAIN_A_V024", "PRESS_TRAIN_A_V025")
code = code.replace("press-train-a-release-presentation-v024", "press-train-a-material-calibration-v025")
exec(compile(code, str(base) + "::v025", "exec"), globals(), globals())
