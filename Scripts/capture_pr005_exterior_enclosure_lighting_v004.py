"""Capture v004 with the established PR005 assembly harness."""

from pathlib import Path


source = Path(__file__).with_name("capture_pr005_exterior_enclosure_assembly_v003.py")
code = source.read_text(encoding="utf-8")
code = code.replace("PR005ExteriorEnclosureAssemblyCandidate_v003", "PR005ExteriorEnclosureLightingCandidate_v004")
code = code.replace("LB_PR005_V003_CAPTURE", "LB_PR005_V004_CAPTURE")
code = code.replace("LB_PR005_V003_CAM_", "LB_PR005_V004_CAM_")
code = code.replace("pr005_exterior_enclosure_assembly_v003", "pr005_exterior_enclosure_lighting_v004")
code = code.replace("pr005_v003_", "pr005_v004_")
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
