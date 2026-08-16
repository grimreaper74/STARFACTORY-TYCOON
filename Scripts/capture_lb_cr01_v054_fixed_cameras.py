"""Capture one CR01 v054 fine-paint fixed camera per process."""

from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
base_path = root / "Scripts/capture_lb_cr01_v042_surfacepaint_fixed_cameras.py"
code = base_path.read_text(encoding="utf-8")

replacements = {
    "CR01 v042 Surface Paint": "CR01 v054 fine-paint candidate",
    "LB_CR01_V042_CAPTURE": "LB_CR01_V054_CAPTURE",
    "LB_CR01_Candidate_v042_SurfacePaintTechnical": "LB_CR01_Candidate_v054_FinePaintVisual",
    "LB_CR01_v042_": "LB_CR01_v054_",
    "Candidate_v042_SurfacePaint": "Candidate_v054_FinePaintVisual",
    "lb_cr01_v042_surfacepaint": "lb_cr01_v054_finepaint_visual",
    "lb-cr01-v042-surfacepaint": "lb-cr01-v054-finepaint-visual",
    "CR01_V042_CAPTURE": "CR01_V054_CAPTURE",
    "v042": "v054",
}

for old, new in replacements.items():
    if old not in code:
        raise RuntimeError(f"v054 capture adapter base drift: missing replacement token {old!r}")
    code = code.replace(old, new)

exec(compile(code, str(base_path) + "::v054-adapter", "exec"), globals(), globals())
