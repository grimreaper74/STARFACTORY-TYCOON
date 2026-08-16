"""Build/apply v004 PBR materials by executing the proven v003 graph builder
against the isolated Candidate_v004 namespace with v004 surface tuning.

The transformation is deliberately narrow and asserted so drift in the base
script fails closed instead of silently targeting the wrong candidate.
"""

from pathlib import Path


source_path = Path(__file__).resolve().with_name("build_apply_pr004_packaging_pbr_v003.py")
source = source_path.read_text(encoding="utf-8")
required = (
    'Candidate_v003', 'packaging_v003', 'PBR_v003',
    '"DullGreyWrap": ("nonmetal", (0.38, 0.42, 0.47, 1.0), 0.16, 11.0, 0.82, 0.20, 0.0, 0.12)',
)
missing = [fragment for fragment in required if fragment not in source]
if missing:
    raise RuntimeError(f"v003 PBR builder drifted; missing asserted fragments: {missing}")

source = source.replace("Candidate_v003", "Candidate_v004")
source = source.replace("candidate_v003", "candidate_v004")
source = source.replace("packaging_v003", "packaging_v004")
source = source.replace("PBR_v003", "PBR_v004")
source = source.replace("pbr-candidate-v003", "pbr-candidate-v004")
source = source.replace("PBR_V003", "PBR_V004")
source = source.replace(
    '"DullGreyWrap": ("nonmetal", (0.38, 0.42, 0.47, 1.0), 0.16, 11.0, 0.82, 0.20, 0.0, 0.12)',
    '"DullGreyWrap": ("nonmetal", (0.31, 0.35, 0.39, 1.0), 0.07, 16.0, 0.78, 0.10, 0.0, 0.06)',
)
source = source.replace(
    '"BandSteel": ("metal", (0.018, 0.022, 0.029, 1.0), 0.30, 8.0, 0.28, 0.32, 1.0, 0.35)',
    '"BandSteel": ("metal", (0.028, 0.034, 0.042, 1.0), 0.20, 10.0, 0.31, 0.22, 1.0, 0.22)',
)
source = source.replace(
    '"EdgeProtector": ("nonmetal", (0.31, 0.13, 0.035, 1.0), 0.36, 8.0, 0.91, 0.42, 0.0, 0.42)',
    '"EdgeProtector": ("nonmetal", (0.28, 0.105, 0.025, 1.0), 0.20, 11.0, 0.88, 0.20, 0.0, 0.20)',
)
exec(compile(source, str(source_path) + "::v004", "exec"), {"__name__": "__main__"})
