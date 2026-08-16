"""Capture one corrected-parent CR01 v053 fixed camera per process."""

from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
base_path = root / "Scripts/capture_lb_cr01_v042_surfacepaint_fixed_cameras.py"
code = base_path.read_text(encoding="utf-8")

replacements = {
    "CR01 v042 Surface Paint": "CR01 v053 corrected-parent candidate",
    "LB_CR01_V042_CAPTURE": "LB_CR01_V053_CAPTURE",
    "LB_CR01_Candidate_v042_SurfacePaintTechnical": "LB_CR01_Candidate_v053_CorrectedParentVisual",
    "LB_CR01_v042_": "LB_CR01_v053_",
    "Candidate_v042_SurfacePaint": "Candidate_v053_CorrectedParentVisual",
    "lb_cr01_v042_surfacepaint": "lb_cr01_v053_corrected_parent_visual",
    "lb-cr01-v042-surfacepaint": "lb-cr01-v053-corrected-parent-visual",
    "CR01_V042_CAPTURE": "CR01_V053_CAPTURE",
    "v042": "v053",
}

for old, new in replacements.items():
    if old not in code:
        raise RuntimeError(f"v053 capture adapter base drift: missing replacement token {old!r}")
    code = code.replace(old, new)

exec(compile(code, str(base_path) + "::v053-adapter", "exec"), globals(), globals())
