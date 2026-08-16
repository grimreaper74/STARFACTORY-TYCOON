"""Build v205 from v198 with the corrected camera-readable service bay."""

from pathlib import Path

source = Path(__file__).with_name("build_press_shop_pr005_release_art_candidate_v203.py")
code = source.read_text(encoding="utf-8")
code = code.replace("v203", "v205").replace("V203", "V205")
code = code.replace("ServiceBayInstalled_v009", "ServiceBayInstalled_v013")
code = code.replace("Static_v009", "Static_v013")
code = code.replace("ServiceBayInstalled_v008", "ServiceBayInstalled_v012")

replacements = {
    '((0.0, -94.0, 120.0), (450.0, 8.0, 230.0))': '((0.0, 94.0, 107.5), (450.0, 8.0, 205.0))',
    '((-205.0, 84.0, 43.5), (18.0, 18.0, 78.0))': '((-205.0, -84.0, 43.5), (18.0, 18.0, 78.0))',
    '((205.0, 84.0, 43.5), (18.0, 18.0, 78.0))': '((205.0, -84.0, 43.5), (18.0, 18.0, 78.0))',
    'unreal.Vector(x, -3406.0, 221.0)': 'unreal.Vector(x, -3274.0, 191.5)',
    '"intensity": 185.0': '"intensity": 20.0',
    '"attenuation_radius": 360.0': '"attenuation_radius": 250.0',
    '"dimensions_mm": [4500, 2000, 2740]': '"dimensions_mm": [4500, 2000, 2450]',
}
for before, after in replacements.items():
    if before not in code:
        raise RuntimeError(f"v205 replacement source missing: {before}")
    code = code.replace(before, after)

exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
