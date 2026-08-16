"""Second corrected direct child of v198; v199-v200 remain dark visual rejects."""

from pathlib import Path

source = Path(__file__).with_name("build_press_shop_pr005_release_art_candidate_v199.py")
code = source.read_text(encoding="utf-8").replace("v199", "v201").replace("V199", "V201")
replacements = {
    "(0.008, 0.028, 0.068), (0.025, 0.085, 0.18)": "(0.070, 0.180, 0.340), (0.150, 0.320, 0.550)",
    "(0.15, 0.035, 0.003), (0.40, 0.12, 0.008)": "(0.350, 0.100, 0.012), (0.650, 0.280, 0.030)",
    "(0.006, 0.009, 0.010), (0.035, 0.042, 0.044)": "(0.025, 0.035, 0.040), (0.100, 0.120, 0.130)",
    "(0.24, 0.10, 0.001), (0.58, 0.28, 0.005)": "(0.400, 0.190, 0.004), (0.750, 0.400, 0.015)",
    "(0.12, 0.14, 0.15), (0.34, 0.37, 0.38)": "(0.300, 0.340, 0.360), (0.550, 0.600, 0.620)",
    "(0.42, 0.44, 0.42), (0.72, 0.74, 0.70)": "(0.680, 0.700, 0.660), (0.900, 0.920, 0.880)",
    '"intensity": 3.0 if index == 1 else 2.2': '"intensity": 6.0 if index == 1 else 30.0',
    '"source_width": 260.0, "source_height": 55.0': '"source_width": 360.0, "source_height": 90.0',
    '"attenuation_radius": 720.0, "cast_shadows": True': '"attenuation_radius": 900.0, "cast_shadows": False',
}
for before, after in replacements.items():
    if before not in code:
        raise RuntimeError(f"v201 replacement source missing: {before}")
    code = code.replace(before, after)
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
