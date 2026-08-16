"""Build isolated CR01 v052 from the proven v042 child-composition importer.

The v052 delta is deliberately constrained to the audited export inventory,
the now-present M20/M25 production meshes, and the corrected stow result.  The
accepted PR-004 map and every earlier CR01 candidate remain untouched.
"""

from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
base_path = root / "Scripts/import_build_lb_cr01_candidate_v042_technical.py"
code = base_path.read_text(encoding="utf-8")

replacements = {
    "Candidate v042": "Candidate v052",
    "Candidate_v042_PayloadRig": "Candidate_v052_PayloadRig",
    "Validation/Candidate_v042/LB_CR01_ExportReimportAudit_v042.json": "Validation/Candidate_v052/LB_CR01_ModularReimportCandidate_v052.json",
    'CANDIDATE_ROOT = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v042"': 'CANDIDATE_ROOT = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v052"',
    'BP_PATH = CANDIDATE_ROOT + "/Blueprints/BP_LB_CR01_CleaningAMR_v042"': 'BP_PATH = CANDIDATE_ROOT + "/Blueprints/BP_LB_CR01_CleaningAMR_v052"',
    'AUDIT_PATH = ROOT / "Saved/Audits/lb_cr01_candidate_v042_unreal_technical_build.json"': 'AUDIT_PATH = ROOT / "Saved/Audits/lb_cr01_candidate_v052_unreal_technical_build.json"',
    'if row["status"] == "PASS_MESH"': 'if row["status"] == "PASS"',
    'if len(meshes) != 20': 'if len(meshes) != 24',
    'and row["source_status"] == "PASS_MESH"': 'and row["source_status"] == "PASS"',
    '"SM_LB_CR01_PayloadUpperStatic_XForwardCM_v042"': '"SM_LB_CR01_PayloadUpperStatic_XForwardCM_v052"',
    '"SM_LB_CR01_Condition_Mothballed_Root_XForwardCM_v042"': '"SM_LB_CR01_Condition_Mothballed_Root_XForwardCM_v052"',
    '"SM_LB_CR01_Condition_Restored_Root_XForwardCM_v042"': '"SM_LB_CR01_Condition_Restored_Root_XForwardCM_v052"',
    '"SM_LB_CR01_Condition_Mothballed_SqueegeeYaw_XForwardCM_v042"': '"SM_LB_CR01_Condition_Mothballed_SqueegeeYaw_XForwardCM_v052"',
    '"SM_LB_CR01_Condition_Restored_SqueegeeYaw_XForwardCM_v042"': '"SM_LB_CR01_Condition_Restored_SqueegeeYaw_XForwardCM_v052"',
    'unreal.Name("LB.Asset.Candidate.v042")': 'unreal.Name("LB.Asset.Candidate.v052")',
    '"$schema": "line-boss/audit/lb-cr01-candidate-v042-unreal-technical-build"': '"$schema": "line-boss/audit/lb-cr01-candidate-v052-unreal-technical-build"',
    '"stow_gate": "FAIL__1252.6377_MM_AT_PUBLISHED_65_DEG_VS_980_PLUS_MINUS_5_MM"': '"stow_gate": "SOURCE_PASS__984.64_MM__FRESH_UNREAL_ASSEMBLY_PROOF_REQUIRED"',
    '"M20 debris-hopper and M25 filter-housing production geometry",': '"M20 debris-hopper and M25 filter-housing source geometry present; Unreal articulation proof remains open",',
    '"compliant carrier-contained side-brush stow mechanism",': '"carrier-contained side-brush stow runtime articulation proof",',
    "v042": "v052",
    "V042": "V052",
}

for old, new in replacements.items():
    if old not in code:
        raise RuntimeError(f"v052 importer base drift: missing replacement token {old!r}")
    code = code.replace(old, new)

exec(compile(code, str(base_path) + "::v052-adapter", "exec"), globals(), globals())
