"""Build v204 from v198 using the handedness-corrected installed service bay."""

from pathlib import Path

source = Path(__file__).with_name("build_press_shop_pr005_release_art_candidate_v203.py")
code = source.read_text(encoding="utf-8")
code = code.replace("v203", "v204").replace("V203", "V204")
code = code.replace("ServiceBayInstalled_v009", "ServiceBayInstalled_v011")
code = code.replace("Static_v009", "Static_v011")
code = code.replace("ServiceBayInstalled_v008", "ServiceBayInstalled_v010")

orientation_replacements = {
    '((0.0, -94.0, 120.0), (450.0, 8.0, 230.0))': '((0.0, 94.0, 120.0), (450.0, 8.0, 230.0))',
    '((-205.0, 84.0, 43.5), (18.0, 18.0, 78.0))': '((-205.0, -84.0, 43.5), (18.0, 18.0, 78.0))',
    '((205.0, 84.0, 43.5), (18.0, 18.0, 78.0))': '((205.0, -84.0, 43.5), (18.0, 18.0, 78.0))',
    'unreal.Vector(x, -3406.0, 221.0)': 'unreal.Vector(x, -3274.0, 221.0)',
}
for before, after in orientation_replacements.items():
    if before not in code:
        raise RuntimeError(f"v204 orientation replacement source missing: {before}")
    code = code.replace(before, after)

exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
