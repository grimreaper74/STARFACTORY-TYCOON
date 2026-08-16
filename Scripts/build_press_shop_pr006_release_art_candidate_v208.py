"""Build fresh v208 from retained v107 with mid-level PR-006 lighting."""

from pathlib import Path

source = Path(__file__).with_name("build_press_shop_pr006_release_art_candidate_v206.py")
code = source.read_text(encoding="utf-8")
code = code.replace("v206", "v208").replace("V206", "V208")
replacements = {
    '(0.035, 0.044, 0.049), 0.72, 0.45': '(0.052, 0.061, 0.065), 0.72, 0.45',
    '(0.17, 0.19, 0.19), 0.48, 0.54': '(0.20, 0.22, 0.22), 0.48, 0.54',
    '("LB_PR006_V054_OperatorTaskLight", 180.0)': '("LB_PR006_V054_OperatorTaskLight", 420.0)',
    '("LB_PR006_V054_DriveTaskLight", 145.0)': '("LB_PR006_V054_DriveTaskLight", 340.0)',
    '"attenuation_radius": 1150.0': '"attenuation_radius": 1500.0',
    '"intensity": 9.0': '"intensity": 18.0',
    '"attenuation_radius": 1250.0': '"attenuation_radius": 1550.0',
    '"broad_rect_intensity": 9.0': '"broad_rect_intensity": 18.0',
    '(-1080, -2860, 285)': '(-1020, -2980, 330)',
    '(-620, -3300, 560)': '(-300, -3500, 620)',
}
for before, after in replacements.items():
    if before not in code:
        raise RuntimeError(f"v208 replacement source missing: {before}")
    code = code.replace(before, after)
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
