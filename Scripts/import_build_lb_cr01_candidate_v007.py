"""Import footprint-corrected LB-CR01 Blender Candidate v006 into isolated Unreal v007."""

from pathlib import Path

root = Path(__file__).resolve().parent
source = (root / "import_build_lb_cr01_candidate_v001.py").read_text(encoding="utf-8")
source = source.replace(
    "Candidate_v002/LB_CR01_CleaningAMR_Candidate_v002.fbx",
    "Candidate_v006/LB_CR01_CleaningAMR_Candidate_v006.fbx",
)
source = source.replace("Candidate v004", "Candidate v007")
source = source.replace("Candidate_v004", "Candidate_v007")
source = source.replace("candidate_v004", "candidate_v007")
source = source.replace("V004", "V007")
source = source.replace("v004", "v007")
exec(compile(source, str(root / "import_build_lb_cr01_candidate_v001.py"), "exec"))
