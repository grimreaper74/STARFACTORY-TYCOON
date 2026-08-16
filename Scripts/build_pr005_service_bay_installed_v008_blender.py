"""Author an installed PR005 service-return bay around the retained logistics kit.

The source is presentation-only and preserves the inherited v053 logistics
datum.  It adds no production mover, route authority, gate or machine value.
"""

from pathlib import Path


source = Path(__file__).with_name("build_pr005_service_logistics_v006_blender.py")
code = source.read_text(encoding="utf-8")
replacements = {
    'SOURCE = ROOT / "SourceAssets/Candidate/PressShop/PR005/ServiceLogistics_v006"':
        'SOURCE = ROOT / "SourceAssets/Candidate/PressShop/PR005/ServiceBayInstalled_v008"',
    'DERIVED = ROOT / "SourceAssets/Candidate/PressShop/PR005/ServiceLogistics_UnrealDerived_v007"':
        'DERIVED = ROOT / "SourceAssets/Candidate/PressShop/PR005/ServiceBayInstalled_UnrealDerived_v009"',
    'ASSET = "SM_CA_MW_PR005_ServiceLogistics_Static_v006"':
        'ASSET = "SM_CA_MW_PR005_ServiceBayInstalled_Static_v008"',
    'DERIVED_ASSET = "SM_CA_MW_PR005_ServiceLogistics_Static_v007"':
        'DERIVED_ASSET = "SM_CA_MW_PR005_ServiceBayInstalled_Static_v009"',
    'PR005_ServiceLogistics_Candidate_v006.blend':
        'PR005_ServiceBayInstalled_Candidate_v008.blend',
    'PR005_SERVICE_LOGISTICS_MANIFEST_v006.json':
        'PR005_SERVICE_BAY_INSTALLED_MANIFEST_v008.json',
    'PR005_SERVICE_LOGISTICS_UNREAL_DERIVED_MANIFEST_v007.json':
        'PR005_SERVICE_BAY_INSTALLED_UNREAL_DERIVED_MANIFEST_v009.json',
    'cairnwell/source/pr005-service-logistics-v006/v1':
        'cairnwell/source/pr005-service-bay-installed-v008/v1',
    'cairnwell/source/pr005-service-logistics-unreal-derived-v007/v1':
        'cairnwell/source/pr005-service-bay-installed-unreal-derived-v009/v1',
    'SIX_RETAINED_V053_LOGISTICS_BLOCKOUT_ACTORS_ONLY':
        'SIX_RETAINED_V053_LOGISTICS_BLOCKOUT_ACTORS_PLUS_PRESENTATION_ONLY_BAY_CONTEXT',
}
for before, after in replacements.items():
    if before not in code:
        raise RuntimeError(f"installed-bay replacement source missing: {before}")
    code = code.replace(before, after)

material_needle = 'rubber = mat("CA_MW_RubberBlack", (0.006, 0.007, 0.007), 0.02, 0.86)\nparts = []'
material_replacement = '''rubber = mat("CA_MW_RubberBlack", (0.006, 0.007, 0.007), 0.02, 0.86)
concrete = mat("CA_MW_SealedConcrete", (0.16, 0.18, 0.19), 0.02, 0.88)
mesh_grey = mat("CA_MW_ServiceMeshGrey", (0.08, 0.095, 0.10), 0.54, 0.52)
parts = []'''
if material_needle not in code:
    raise RuntimeError("installed-bay material insertion point missing")
code = code.replace(material_needle, material_replacement)

join_needle = 'bpy.ops.object.select_all(action="DESELECT")\nfor part in parts:'
installed_context = r'''# Lift the retained detailed kit onto a shallow authored service-bay inset.
for part in parts:
    part.location.z += 0.045

# 4.5 m x 2.0 m sealed-concrete service-return pad at the inherited datum.
parts.append(box("ServiceBayPad", (4.50, 2.00, 0.04), (0.0, 0.0, 0.02), concrete, 0.0))
for name, dimensions, location in (
    ("BoundaryRear", (4.50, 0.05, 0.016), (0.0, 0.975, 0.052)),
    ("BoundaryFrontLeft", (1.55, 0.05, 0.016), (-1.475, -0.975, 0.052)),
    ("BoundaryFrontRight", (1.55, 0.05, 0.016), (1.475, -0.975, 0.052)),
    ("BoundaryLeft", (0.05, 2.00, 0.016), (-2.225, 0.0, 0.052)),
    ("BoundaryRight", (0.05, 2.00, 0.016), (2.225, 0.0, 0.052)),
):
    parts.append(box(name, dimensions, location, yellow, 0.002))

# Rear open-mesh service screen: installed context, not a production guard.
rear_y = 0.94
for x in (-2.20, -1.10, 0.0, 1.10, 2.20):
    parts.append(box("ServiceScreenPost", (0.065, 0.065, 2.30), (x, rear_y, 1.20), yellow, 0.006))
for z in (0.18, 1.18, 2.30):
    parts.append(box("ServiceScreenRail", (4.46, 0.055, 0.065), (0.0, rear_y, z), yellow, 0.005))
for x_index in range(-14, 15):
    x = x_index * 0.15
    parts.append(box("ServiceMeshVertical", (0.012, 0.020, 1.90), (x, rear_y - 0.035, 1.22), mesh_grey, 0.001))
for z_index in range(0, 9):
    z = 0.32 + z_index * 0.225
    parts.append(box("ServiceMeshHorizontal", (4.20, 0.020, 0.012), (0.0, rear_y - 0.035, z), mesh_grey, 0.001))

# Integrated identity plate and source-authored task fixtures.
parts.append(box("ServiceBayIdentityPlate", (2.95, 0.05, 0.38), (0.0, rear_y - 0.065, 2.55), blue, 0.012))
parts.append(raised_text("ServiceBayIdentity", "PR-005  SERVICE RETURN", (0.0, rear_y - 0.096, 2.56), 0.145, white))
for x in (-1.05, 1.05):
    parts.append(box("TaskFixtureBody", (1.35, 0.22, 0.10), (x, 0.66, 2.27), charcoal, 0.012))
    parts.append(box("TaskFixtureLens", (1.18, 0.24, 0.025), (x, 0.65, 2.205), white, 0.005))

# Front dock protection keeps the bay entry legible without closing it.
for x in (-2.05, 2.05):
    parts.append(cylinder("ServiceBayBollard", 0.085, 0.78, (x, -0.84, 0.435), (0.0, 0.0, 0.0), yellow, 32))
    parts.append(cylinder("ServiceBayBollardFoot", 0.16, 0.025, (x, -0.84, 0.057), (0.0, 0.0, 0.0), charcoal, 32))
    for z in (0.25, 0.50, 0.70):
        parts.append(cylinder("BollardReflectiveBand", 0.088, 0.045, (x, -0.84, z), (0.0, 0.0, 0.0), white, 32))

bpy.ops.object.select_all(action="DESELECT")
for part in parts:'''
if join_needle not in code:
    raise RuntimeError("installed-bay geometry insertion point missing")
code = code.replace(join_needle, installed_context)

slot_needle = '"CA_MW_HardwareSteel", "CA_MW_LabelWhite", "CA_MW_RubberBlack"],'
slot_replacement = '"CA_MW_HardwareSteel", "CA_MW_LabelWhite", "CA_MW_RubberBlack",\n        "CA_MW_SealedConcrete", "CA_MW_ServiceMeshGrey"],'
if slot_needle not in code:
    raise RuntimeError("installed-bay material-slot insertion point missing")
code = code.replace(slot_needle, slot_replacement)

exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
