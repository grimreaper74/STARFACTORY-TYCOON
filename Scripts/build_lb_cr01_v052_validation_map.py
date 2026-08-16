"""Build the isolated fixed-camera visual review map for CR01 v052."""

from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
base_path = root / "Scripts/build_lb_cr01_v042_surfacepaint_validation_map.py"
code = base_path.read_text(encoding="utf-8")

replacements = {
    "CR01 v042": "CR01 v052",
    "LB_CR01_Candidate_v042_SurfacePaintTechnical": "LB_CR01_Candidate_v052_ReleaseVisual",
    "/Candidate_v042/Blueprints/BP_LB_CR01_CleaningAMR_v042": "/Candidate_v052/Blueprints/BP_LB_CR01_CleaningAMR_v052",
    "lb_cr01_v042_surfacepaint_validation_map.json": "lb_cr01_v052_validation_map.json",
    "v042": "v052",
    "V042": "V052",
    'if "BodyCharcoal" in slot_name or "FrameAnthracite" in slot_name:': 'if any(token in slot_name for token in ("BodyCharcoal", "FrameAnthracite", "GraphitePowdercoat", "ServiceCharcoal")):',
    'if "CairnwellGreen" in slot_name:': 'if "CairnwellGreen" in slot_name or "RuggedGreen" in slot_name:',
    'unreal.Name("LB.CR01.StowConflictOpen"),': 'unreal.Name("LB.CR01.StowSourcePass.RuntimeProofOpen"),',
    '"stow_conflict": "OPEN__DEFAULT_POSE_IS_NOT_TRAVEL_AUTHORITY"': '"stow_gate": "SOURCE_PASS__984.64_MM__FRESH_UNREAL_RUNTIME_ARTICULATION_PROOF_OPEN"',
}

for old, new in replacements.items():
    if old not in code:
        raise RuntimeError(f"v052 visual-map adapter base drift: missing replacement token {old!r}")
    code = code.replace(old, new)

exec(compile(code, str(base_path) + "::v052-adapter", "exec"), globals(), globals())
