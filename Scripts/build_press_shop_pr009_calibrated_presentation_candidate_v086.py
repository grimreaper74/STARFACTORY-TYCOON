"""Build v086 from retained v085 with measured identity placement and darker calibration."""
from pathlib import Path

base = Path(__file__).with_name("build_press_shop_pr009_layered_presentation_candidate_v085.py")
code = base.read_text(encoding="utf-8")

# Preserve v085 as the new base while versioning every new v086 artifact.
code = code.replace(
    'BASE = "/Game/LineBoss/Maps/LB_PressShop_PR009CorrectedIntegrationCandidate_v084"',
    'BASE = "__PR009_V086_BASE__"')
code = code.replace('OLD_PREFIX = "LB_PR009_V084_"', 'OLD_PREFIX = "__PR009_V086_OLD_PREFIX__"')
code = code.replace("v085", "v086").replace("V085", "V086")
code = code.replace("__PR009_V086_BASE__", "/Game/LineBoss/Maps/LB_PressShop_PR009LayeredPresentationCandidate_v085")
code = code.replace("__PR009_V086_OLD_PREFIX__", "LB_PR009_V085_")

# Reduce the high-key response seen in all four fresh v085 cameras.
replacements = {
    "(0.025, 0.105, 0.084), (0.065, 0.205, 0.165)":
        "(0.018, 0.075, 0.060), (0.042, 0.150, 0.115)",
    "(0.54, 0.285, 0.003), (0.82, 0.50, 0.012)":
        "(0.36, 0.17, 0.002), (0.62, 0.32, 0.008)",
    "(0.27, 0.295, 0.285), (0.43, 0.46, 0.44)":
        "(0.15, 0.17, 0.165), (0.29, 0.32, 0.305)",
    "(0.36, 0.405, 0.435), (0.68, 0.72, 0.75)":
        "(0.25, 0.285, 0.305), (0.52, 0.57, 0.60)",
    "(0.44, 0.49, 0.52), (0.76, 0.80, 0.82)":
        "(0.31, 0.35, 0.37), (0.62, 0.66, 0.68)",
    '"intensity": 300.0': '"intensity": 180.0',
    '"influence_radius": 900.0, "brightness": 0.72':
        '"influence_radius": 900.0, "brightness": 0.56',
    "(600.0, -2264.0, 202.0), (210.0, 3.0, 58.0)":
        "(600.0, -1738.5, 165.0), (210.0, 3.0, 58.0)",
    "(600.0, -2266.0, 217.0)": "(600.0, -1736.0, 180.0)",
    "(600.0, -2266.0, 202.0)": "(600.0, -1736.0, 165.0)",
    "(600.0, -2266.0, 187.0)": "(600.0, -1736.0, 150.0)",
    "camera(\"Process\", (-590, -1220, 565), (285, -2000, 130), 50)":
        "camera(\"Process\", (-620, -1190, 525), (310, -1990, 125), 52)",
    "camera(\"Interface\", (-180, -1390, 325), (145, -2000, 108), 41)":
        "camera(\"Interface\", (-250, -1240, 300), (170, -1995, 105), 46)",
    "camera(\"CellHero\", (1190, -1260, 520), (600, -2000, 150), 47)":
        "camera(\"CellHero\", (1210, -1220, 475), (600, -1995, 135), 51)",
    "camera(\"Elevated\", (310, -1090, 820), (510, -2000, 135), 53)":
        "camera(\"Elevated\", (250, -1080, 700), (520, -1995, 120), 55)",
    "PR009_V086_EXPLICIT_AUTHORED_ROLE_LAYERED_MATERIAL_IDENTITY_AND_CALIBRATED_PRESENTATION_BUILD_PASS":
        "PR009_V086_DARKER_CALIBRATION_MEASURED_NEAR_GUARD_IDENTITY_AND_CAMERA_REFINEMENT_BUILD_PASS",
}
for old, new in replacements.items():
    if old not in code:
        raise RuntimeError(f"v086 adapter source token missing: {old}")
    code = code.replace(old, new)

exec(compile(code, str(base) + "::v086-calibrated-adapter", "exec"), globals(), globals())
