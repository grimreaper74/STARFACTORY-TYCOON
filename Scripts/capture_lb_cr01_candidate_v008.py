"""Capture one fixed-camera LB-CR01 Unreal Candidate v008 evidence image."""

from pathlib import Path

root = Path(__file__).resolve().parent
source = (root / "capture_lb_cr01_candidate_v002.py").read_text(encoding="utf-8")
source = source.replace("Candidate_v004", "Candidate_v008")
source = source.replace("Candidate v004", "Candidate v008")
source = source.replace("V004", "V008")
source = source.replace("v004", "v008")
exec(compile(source, str(root / "capture_lb_cr01_candidate_v002.py"), "exec"))
