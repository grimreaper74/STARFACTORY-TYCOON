"""Corrected v200 direct child of v198; v199 is a dark visual reject."""

from pathlib import Path

source = Path(__file__).with_name("build_press_shop_pr005_release_art_candidate_v199.py")
code = source.read_text(encoding="utf-8").replace("v199", "v200").replace("V199", "V200")
replacements = {
    "(0.008, 0.028, 0.068), (0.025, 0.085, 0.18)": "(0.025, 0.080, 0.180), (0.060, 0.180, 0.350)",
    "(0.15, 0.035, 0.003), (0.40, 0.12, 0.008)": "(0.280, 0.070, 0.008), (0.550, 0.220, 0.020)",
    "(0.006, 0.009, 0.010), (0.035, 0.042, 0.044)": "(0.015, 0.022, 0.025), (0.060, 0.080, 0.090)",
    "(0.24, 0.10, 0.001), (0.58, 0.28, 0.005)": "(0.350, 0.160, 0.002), (0.700, 0.350, 0.008)",
    "(0.12, 0.14, 0.15), (0.34, 0.37, 0.38)": "(0.220, 0.250, 0.270), (0.450, 0.500, 0.520)",
    "(0.42, 0.44, 0.42), (0.72, 0.74, 0.70)": "(0.600, 0.620, 0.580), (0.820, 0.840, 0.800)",
    '"intensity": 3.0 if index == 1 else 2.2': '"intensity": 4.0 if index == 1 else 8.0',
    '"source_width": 260.0, "source_height": 55.0': '"source_width": 320.0, "source_height": 80.0',
    '"attenuation_radius": 720.0, "cast_shadows": True': '"attenuation_radius": 850.0, "cast_shadows": False',
}
for before, after in replacements.items():
    if before not in code:
        raise RuntimeError(f"v200 replacement source missing: {before}")
    code = code.replace(before, after)
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
