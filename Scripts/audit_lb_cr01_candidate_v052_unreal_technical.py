"""Fresh-process technical audit adapter for isolated CR01 v052."""

from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
base_path = root / "Scripts/audit_lb_cr01_candidate_v042_unreal_technical.py"
code = base_path.read_text(encoding="utf-8")

replacements = {
    "quarantined CR01 v042": "quarantined CR01 v052",
    "lb_cr01_candidate_v042_unreal_technical_build.json": "lb_cr01_candidate_v052_unreal_technical_build.json",
    "lb_cr01_candidate_v042_unreal_technical_independent.json": "lb_cr01_candidate_v052_unreal_technical_independent.json",
    'CANDIDATE_ROOT = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v042"': 'CANDIDATE_ROOT = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v052"',
    'BP_PATH = CANDIDATE_ROOT + "/Blueprints/BP_LB_CR01_CleaningAMR_v042"': 'BP_PATH = CANDIDATE_ROOT + "/Blueprints/BP_LB_CR01_CleaningAMR_v052"',
    '"LB_CR01_v042_DisposableTechnicalAudit"': '"LB_CR01_v052_DisposableTechnicalAudit"',
    'expects_mesh = stage["role"] not in {"carrier", "required_source_geometry"}': 'expects_mesh = True',
    'if len(mesh_paths) != 20:': 'if len(mesh_paths) != 24:',
    'f"Expected 20 imported StaticMeshes, found {len(mesh_paths)}"': 'f"Expected 24 imported StaticMeshes, found {len(mesh_paths)}"',
    'payload_path = MESH_ROOT + "/SM_LB_CR01_PayloadUpperStatic_XForwardCM_v042"': 'payload_path = MESH_ROOT + "/SM_LB_CR01_PayloadUpperStatic_XForwardCM_v052"',
    '(150.3, 98.464, 79.7)': '(151.05002, 98.464, 95.58982)',
    'if len(material_binding_rows) != 58:': 'if len(material_binding_rows) != 96:',
    'f"Expected 58 CR01 effective material bindings, found {len(material_binding_rows)}"': 'f"Expected 96 CR01 effective material bindings, found {len(material_binding_rows)}"',
    'if shared_paint_binding_count != 28:': 'if shared_paint_binding_count != 40:',
    'f"Expected 28 shared-paint v002 bindings, found {shared_paint_binding_count}"': 'f"Expected 40 shared-paint v002 bindings, found {shared_paint_binding_count}"',
    '"$schema": "line-boss/audit/lb-cr01-candidate-v042-unreal-technical-independent"': '"$schema": "line-boss/audit/lb-cr01-candidate-v052-unreal-technical-independent"',
    '"stow_gate": "FAIL__PUBLISHED_RANGE_ONLY_REACHES_1252.6377_MM"': '"stow_gate": "SOURCE_PASS__984.64_MM__RUNTIME_ARTICULATION_PROOF_OPEN"',
    "CR01_V042_TECHNICAL": "CR01_V052_TECHNICAL",
    "v042": "v052",
}

for old, new in replacements.items():
    if old not in code:
        raise RuntimeError(f"v052 audit adapter base drift: missing replacement token {old!r}")
    code = code.replace(old, new)

exec(compile(code, str(base_path) + "::v052-adapter", "exec"), globals(), globals())
