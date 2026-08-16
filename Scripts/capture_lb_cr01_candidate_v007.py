"""Capture one fixed-camera LB-CR01 Unreal Candidate v007 evidence image."""

from pathlib import Path

root = Path(__file__).resolve().parent
source = (root / "capture_lb_cr01_candidate_v002.py").read_text(encoding="utf-8")
source = source.replace("Candidate_v004", "Candidate_v007")
source = source.replace("Candidate v004", "Candidate v007")
source = source.replace("V004", "V007")
source = source.replace("v004", "v007")
exec(compile(source, str(root / "capture_lb_cr01_candidate_v002.py"), "exec"))
