"""Build CR01 v054 fine-paint fixed-camera comparison map."""

from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
base_path = root / "Scripts/build_lb_cr01_v042_surfacepaint_validation_map.py"
code = base_path.read_text(encoding="utf-8")

replacements = {
    "CR01 v042": "CR01 v054",
    "LB_CR01_Candidate_v042_SurfacePaintTechnical": "LB_CR01_Candidate_v054_FinePaintVisual",
    "/Candidate_v042/Blueprints/BP_LB_CR01_CleaningAMR_v042": "/Candidate_v054/Blueprints/BP_LB_CR01_CleaningAMR_v054",
    "/Game/LineBoss/Robots/Shared/Materials/Candidate_v002": "/Game/LineBoss/Robots/Shared/Materials/Candidate_v003",
    'f"{SHARED_PAINT_ROOT}/MI_LB_Robot_{semantic}_{condition}_v002"': 'f"{SHARED_PAINT_ROOT}/MI_LB_Robot_{semantic}_{condition}_v003"',
    "lb_cr01_v042_surfacepaint_validation_map.json": "lb_cr01_v054_validation_map.json",
    'for semantic in ("BodyCharcoal", "SafetyYellow", "CairnwellGreen", "ServiceGrey"):': 'for semantic in ("BodyCharcoal", "SafetyYellow", "CairnwellGreen", "ServiceGrey", "MarkingWarmWhite"):',
    'if "BodyCharcoal" in slot_name or "FrameAnthracite" in slot_name:': 'if any(token in slot_name for token in ("BodyCharcoal", "FrameAnthracite", "GraphitePowdercoat")):',
    'if "SafetyYellow" in slot_name:': 'if any(token in slot_name for token in ("SafetyYellow", "FunctionSafetyYellow", "CairnwellSafetyYellow")):',
    'if "CairnwellGreen" in slot_name:': 'if "CairnwellGreen" in slot_name or "RuggedGreen" in slot_name:',
    'return paint["ServiceGrey_Restored"]': 'return paint["MarkingWarmWhite_Restored"]',
    'if mesh is None or not mesh.get_path_name().startswith("/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v042/Meshes/"):': 'if mesh is None or not (mesh.get_path_name().startswith("/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v052/Meshes/") or mesh.get_path_name().startswith("/Game/LineBoss/Robots/Shared/RP01/Candidate_v001/Meshes/")):',
    "LB_CR01_v042_": "LB_CR01_v054_",
    "LB.Validation.CR01.v042": "LB.Validation.CR01.v054",
    '"intensity": 2.2': '"intensity": 1.15',
    '"intensity", 0.8': '"intensity", 0.42',
    '("MothFill", (300.0, -430.0, 250.0), 650.0)': '("MothFill", (300.0, -430.0, 250.0), 260.0)',
    '("RestoredFill", (300.0, 430.0, 250.0), 650.0)': '("RestoredFill", (300.0, 430.0, 250.0), 260.0)',
    '("Rim", (-100.0, 0.0, 320.0), 480.0)': '("Rim", (-100.0, 0.0, 320.0), 220.0)',
    '"auto_exposure_bias": -0.3': '"auto_exposure_bias": -0.75',
    '"exposure_bias": -0.3': '"exposure_bias": -0.75',
    'unreal.Name("LB.CR01.StowConflictOpen"),': 'unreal.Name("LB.CR01.StowSourcePass.RuntimeProofOpen"),',
    '"stow_conflict": "OPEN__DEFAULT_POSE_IS_NOT_TRAVEL_AUTHORITY"': '"stow_gate": "SOURCE_PASS__984.64_MM__FRESH_UNREAL_RUNTIME_ARTICULATION_PROOF_OPEN"',
    "V042": "V054",
    "v042": "v054",
}

for old, new in replacements.items():
    if old not in code:
        raise RuntimeError(f"v054 visual-map adapter base drift: missing replacement token {old!r}")
    code = code.replace(old, new)

exec(compile(code, str(base_path) + "::v054-adapter", "exec"), globals(), globals())
