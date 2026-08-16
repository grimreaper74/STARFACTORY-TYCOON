"""Import and assemble isolated PR-004 Candidate_v007 with flexible film v007.

All writes remain below Candidate_v007 and its dedicated validation map. The
stable family key stays film_dewrap_v004 because the base assembler uses it for
placement and parent contracts; the source, assets and destination are v007.
No permanent Press Shop content is touched and promotion is forbidden.
"""

import importlib.util
from pathlib import Path
import sys


SCRIPT = Path(__file__).resolve().with_name("import_build_pr004_depackaging_candidate.py")
spec = importlib.util.spec_from_file_location("line_boss_pr004_candidate_import_base_v007", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to load base importer {SCRIPT}")
base = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = base
spec.loader.exec_module(base)

base.DESTINATION_ROOT = "/Game/LineBoss/Stations/Press/PR004/Candidate_v007"
base.MATERIAL_ROOT = base.DESTINATION_ROOT + "/Materials"
base.VALIDATION_MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Depackaging_Candidate_v007"
base.PREFLIGHT_AUDIT = base.CANONICAL_REPO / "Saved/Audits/pr004_unreal_import_preflight_v007.json"
base.IMPORT_AUDIT = base.CANONICAL_REPO / "Saved/Audits/pr004_unreal_import_candidate_v007.json"

base.FAMILY_SPECS = tuple(
    {**family, "destination": str(family["destination"]).replace("/Candidate_v001/", "/Candidate_v007/")}
    for family in base.FAMILY_SPECS
) + (
    {
        "id": "packaging_v004",
        "manifest": base.CANONICAL_REPO / "SourceAssets/PR004/PackagingRig_v004/pr004_packaging_rig_candidate_v004_manifest.json",
        "audit": base.CANONICAL_REPO / "Saved/Audits/pr004_packaging_rig_candidate_v004_independent_fbx_uv_audit.json",
        "version": "v004",
        "expected_modules": 43,
        "destination": base.DESTINATION_ROOT + "/PackagingRig_v004",
        "requires_independent_fbx_pass": True,
    },
    {
        "id": "film_dewrap_v004",
        "manifest": base.CANONICAL_REPO / "SourceAssets/PR004/FilmDewrapSpindle_v007/pr004_film_dewrap_spindle_candidate_v007_manifest.json",
        "audit": base.CANONICAL_REPO / "Saved/Audits/pr004_film_dewrap_spindle_candidate_v007_independent.json",
        "version": "v007",
        "expected_modules": 14,
        "destination": base.DESTINATION_ROOT + "/FilmDewrap_v007",
        "requires_independent_fbx_pass": True,
    },
)

raise SystemExit(base.main())
