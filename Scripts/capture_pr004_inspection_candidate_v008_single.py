"""Request one deterministic PR-004 Candidate_v008 screenshot per session."""

from pathlib import Path


source_path = Path(__file__).resolve().with_name("capture_pr004_depackaging_candidate_v004_single.py")
source = source_path.read_text(encoding="utf-8")
source = source.replace("LB_PR004_Depackaging_Candidate_v004", "LB_PR004_Inspection_Candidate_v008")
source = source.replace("Candidate_v004", "Candidate_v008")
source = source.replace("candidate_v004", "candidate_v008")
source = source.replace("_v004", "_v008")
source = source.replace("V004", "V008")
exec(compile(source, str(source_path), "exec"), globals(), globals())
