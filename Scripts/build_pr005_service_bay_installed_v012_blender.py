"""Camera-readable installed PR005 service-return bay source successor."""

from pathlib import Path


source = Path(__file__).with_name("build_pr005_service_bay_installed_v008_blender.py")
code = source.read_text(encoding="utf-8")
code = code.replace("ServiceBayInstalled_v008", "ServiceBayInstalled_v012")
code = code.replace("ServiceBayInstalled_UnrealDerived_v009", "ServiceBayInstalled_UnrealDerived_v013")
code = code.replace("Static_v008", "Static_v012")
code = code.replace("Static_v009", "Static_v013")
code = code.replace("Candidate_v008", "Candidate_v012")
code = code.replace("MANIFEST_v008", "MANIFEST_v012")
code = code.replace("MANIFEST_v009", "MANIFEST_v013")
code = code.replace("installed-v008", "installed-v012")
code = code.replace("derived-v009", "derived-v013")

replacements = {
    "rear_y = 0.94": "rear_y = -0.94",
    '(0.065, 0.065, 2.30), (x, rear_y, 1.20)': '(0.065, 0.065, 2.05), (x, rear_y, 1.075)',
    'for z in (0.18, 1.18, 2.30):': 'for z in (0.18, 1.05, 2.05):',
    '(0.012, 0.020, 1.90), (x, rear_y - 0.035, 1.22)': '(0.012, 0.020, 1.65), (x, rear_y - 0.035, 1.07)',
    'for z_index in range(0, 9):': 'for z_index in range(0, 8):',
    '(0.0, rear_y - 0.065, 2.55)': '(0.0, rear_y + 0.065, 2.26)',
    'parts.append(raised_text("ServiceBayIdentity", "PR-005  SERVICE RETURN", (0.0, rear_y - 0.096, 2.56), 0.145, white))':
        'identity = raised_text("ServiceBayIdentity", "PR-005  SERVICE RETURN", (0.0, rear_y + 0.096, 2.27), 0.145, white)\n'
        'identity.rotation_euler = (math.radians(90.0), 0.0, math.radians(180.0))\n'
        'parts.append(identity)',
    '(x, 0.66, 2.27)': '(x, -0.66, 1.98)',
    '(x, 0.65, 2.205)': '(x, -0.65, 1.915)',
    '(x, -0.84, 0.435)': '(x, 0.84, 0.435)',
    '(x, -0.84, 0.057)': '(x, 0.84, 0.057)',
    '(x, -0.84, z)': '(x, 0.84, z)',
}
for before, after in replacements.items():
    if before not in code:
        raise RuntimeError(f"v012 source correction point missing: {before}")
    code = code.replace(before, after)

exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
