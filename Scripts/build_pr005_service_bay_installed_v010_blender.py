"""Handedness-corrected installed PR005 service-return bay source successor."""

from pathlib import Path


source = Path(__file__).with_name("build_pr005_service_bay_installed_v008_blender.py")
code = source.read_text(encoding="utf-8")
code = code.replace("ServiceBayInstalled_v008", "ServiceBayInstalled_v010")
code = code.replace("ServiceBayInstalled_UnrealDerived_v009", "ServiceBayInstalled_UnrealDerived_v011")
code = code.replace("Static_v008", "Static_v010")
code = code.replace("Static_v009", "Static_v011")
code = code.replace("Candidate_v008", "Candidate_v010")
code = code.replace("MANIFEST_v008", "MANIFEST_v010")
code = code.replace("MANIFEST_v009", "MANIFEST_v011")
code = code.replace("installed-v008", "installed-v010")
code = code.replace("derived-v009", "derived-v011")

orientation_replacements = {
    "rear_y = 0.94": "rear_y = -0.94",
    "(0.0, rear_y - 0.065, 2.55)": "(0.0, rear_y + 0.065, 2.55)",
    "(0.0, rear_y - 0.096, 2.56)": "(0.0, rear_y + 0.096, 2.56)",
    "(x, 0.66, 2.27)": "(x, -0.66, 2.27)",
    "(x, 0.65, 2.205)": "(x, -0.65, 2.205)",
    "(x, -0.84, 0.435)": "(x, 0.84, 0.435)",
    "(x, -0.84, 0.057)": "(x, 0.84, 0.057)",
    "(x, -0.84, z)": "(x, 0.84, z)",
}
for before, after in orientation_replacements.items():
    if before not in code:
        raise RuntimeError(f"v010 orientation replacement source missing: {before}")
    code = code.replace(before, after)

exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
