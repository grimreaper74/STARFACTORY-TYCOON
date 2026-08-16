"""Launch the quarantined PR-004 v002 Unreal preflight/import assembly.

This extends the proven candidate-only importer with the independently audited
film-dewrapper v004 mechanics.  The rejected packaging rigs remain excluded.
All writes stay below Candidate_v002 and the dedicated developer validation
map; there is deliberately no promotion path.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


SCRIPT = Path(__file__).resolve().with_name("import_build_pr004_depackaging_candidate.py")
spec = importlib.util.spec_from_file_location("line_boss_pr004_candidate_import_base", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to load base importer {SCRIPT}")
base = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = base
spec.loader.exec_module(base)

base.DESTINATION_ROOT = "/Game/LineBoss/Stations/Press/PR004/Candidate_v002"
base.MATERIAL_ROOT = base.DESTINATION_ROOT + "/Materials"
base.VALIDATION_MAP = "/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Depackaging_Candidate_v002"
base.PREFLIGHT_AUDIT = base.CANONICAL_REPO / "Saved/Audits/pr004_unreal_import_preflight_v002.json"
base.IMPORT_AUDIT = base.CANONICAL_REPO / "Saved/Audits/pr004_unreal_import_candidate_v002.json"

base.FAMILY_SPECS = tuple(
    {**family, "destination": str(family["destination"]).replace("/Candidate_v001/", "/Candidate_v002/")}
    for family in base.FAMILY_SPECS
) + (
    {
        "id": "film_dewrap_v004",
        "manifest": base.CANONICAL_REPO / "SourceAssets/PR004/FilmDewrapSpindle_v004/pr004_film_dewrap_spindle_candidate_v004_manifest.json",
        "audit": base.CANONICAL_REPO / "Saved/Audits/pr004_film_dewrap_spindle_candidate_v004_independent.json",
        "version": "v004",
        "expected_modules": 11,
        "destination": base.DESTINATION_ROOT + "/FilmDewrap_v004",
        "requires_independent_fbx_pass": True,
    },
    {
        "id": "process_context_v001",
        "manifest": base.CANONICAL_REPO / "SourceAssets/PR004/ProcessContext_v001/pr004_process_context_candidate_v001_manifest.json",
        "audit": base.CANONICAL_REPO / "Saved/Audits/pr004_process_context_candidate_v001_independent.json",
        "version": "v001",
        "expected_modules": 5,
        "destination": base.DESTINATION_ROOT + "/ProcessContext_v001",
        "requires_independent_fbx_pass": True,
        "module_version_overrides": {"packaged_master_coil": "v003"},
    },
)

raise SystemExit(base.main())
