"""Import the shared-platform LB-CR01 Candidate v005 into an isolated Unreal v006 namespace.

The Blender source remains a visual candidate.  This wrapper deliberately keeps the
old Unreal candidate and full-shop map untouched while reusing the proven modular
import/evidence harness.
"""

from pathlib import Path

root = Path(__file__).resolve().parent
source = (root / "import_build_lb_cr01_candidate_v001.py").read_text(encoding="utf-8")
source = source.replace(
    "Candidate_v002/LB_CR01_CleaningAMR_Candidate_v002.fbx",
    "Candidate_v005/LB_CR01_CleaningAMR_Candidate_v005.fbx",
)
source = source.replace("Candidate v004", "Candidate v006")
source = source.replace("Candidate_v004", "Candidate_v006")
source = source.replace("candidate_v004", "candidate_v006")
source = source.replace("V004", "V006")
source = source.replace("v004", "v006")
exec(compile(source, str(root / "import_build_lb_cr01_candidate_v001.py"), "exec"))
