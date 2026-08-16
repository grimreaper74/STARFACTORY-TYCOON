"""Build v003 with explicit FBX smoothing data and camera-readable sheet/panel angles."""

from pathlib import Path

base = Path(__file__).with_name("build_press_train_crown_endpoint_presentation_v001.py")
code = base.read_text(encoding="utf-8")
for old, new in (
    ("CrownEndpointPresentation_v001", "CrownEndpointPresentation_v003"),
    ("CROWN_ENDPOINT_PRESENTATION_MANIFEST_v001", "CROWN_ENDPOINT_PRESENTATION_MANIFEST_v003"),
    ("CrownEndpointPresentation_v001.blend", "CrownEndpointPresentation_v003.blend"),
    ("crown-endpoint-presentation-v001", "crown-endpoint-presentation-v003"),
    ("CROWN_ENDPOINT_PRESENTATION_V001", "CROWN_ENDPOINT_PRESENTATION_V003"),
    ("_v001", "_v003"),
):
    code = code.replace(old, new)

# Preserve the quieter v002 crown calibration.
code = code.replace(
    'box(parts, "OperatorDrivePlinth", (520, 2600, 1220), (2670, 0, 40), "CA_MW_CairnwellGreen", 55)',
    'box(parts, "OperatorDrivePlinth", (420, 2200, 900), (2640, 0, 30), "CA_MW_CairnwellGreen", 48)',
)
code = code.replace(
    'cylinder(parts, "OperatorFlywheelGuard", 1120, 420, (2930, -720, 120), "CA_MW_ServiceGrey", axis="X", vertices=32)',
    'cylinder(parts, "OperatorFlywheelGuard", 620, 280, (2890, -620, 80), "CA_MW_ServiceGrey", axis="X", vertices=28)',
)
code = code.replace(
    'box(parts, "OperatorVentBank", (210, 1050, 620), (2980, 720, 20), "CA_MW_FoundryCharcoal", 22)',
    'box(parts, "OperatorVentBank", (150, 900, 480), (2885, 580, 20), "CA_MW_FoundryCharcoal", 18)',
)
code = code.replace(
    'box(parts, f"DriveVent_{y}", (105, 160, 460), (3100, y, 20), "CA_MW_WorkedSteel", 6)',
    'box(parts, f"DriveVent_{y}", (85, 125, 330), (2980, y - 140, 20), "CA_MW_WorkedSteel", 5)',
)
code = code.replace(
    'box(parts, "FeedWitnessBand", (135, 4300, 160), (2460, 1200, 920), "CA_MW_TrainAAccent", 12)',
    'box(parts, "FeedWitnessBand", (135, 4000, 160), (2460, 1100, 920), "CA_MW_TrainAAccent", 12)',
)

# Export actual smoothing groups instead of relying on Unreal's fallback normal
# generation. This is the clean successor to the warning-bearing v002 FBXs.
code = code.replace(
    'use_mesh_modifiers=True, add_leaf_bones=False,',
    'use_mesh_modifiers=True, mesh_smooth_type="FACE", add_leaf_bones=False,',
)

# Tilt visible sheet surfaces around local Y so the operator/CCTV camera sees
# material state rather than an almost edge-on strip. This changes presentation
# only and remains inside the existing planning envelopes.
code = code.replace(
    'def box(parts, name, dims, loc, material, bevel=0, rotation_z=0.0):',
    'def box(parts, name, dims, loc, material, bevel=0, rotation_z=0.0, rotation_y=0.0):',
)
code = code.replace(
    'obj.rotation_euler[2] = math.radians(rotation_z)',
    'obj.rotation_euler[2] = math.radians(rotation_z)\n    obj.rotation_euler[1] = math.radians(rotation_y)',
)
code = code.replace(
    'box(parts, "EnteringBlank", (4520, 1650, 58), (0, 250, 1120), "CA_MW_WorkedSteel", 7)',
    'box(parts, "EnteringBlank", (4520, 1650, 72), (0, 250, 1210), "CA_MW_WorkedSteel", 7, rotation_y=-6)',
)
code = code.replace(
    'box(parts, "RaisedTopBlank", (4420, 2250, 58), (0, 1950, 1220), "CA_MW_WorkedSteel", 7)',
    'box(parts, "RaisedTopBlank", (4420, 2250, 72), (0, 1950, 1360), "CA_MW_WorkedSteel", 7, rotation_y=-8)',
)
code = code.replace('(x, 1950, 1360)', '(x, 1950, 1580)')
code = code.replace(
    'box(parts, f"{prefix}_Centre", (3500, 1450, 62), (0, y, z), material, 18)',
    'box(parts, f"{prefix}_Centre", (3500, 1450, 88), (0, y, z), material, 18, rotation_y=-12)',
)
code = code.replace(
    'box(parts, f"{prefix}_WingL", (850, 1300, 62), (-2050, y, z + 35), material, 18, rotation_z=-10)',
    'box(parts, f"{prefix}_WingL", (850, 1300, 88), (-2050, y, z + 35), material, 18, rotation_z=-10, rotation_y=-12)',
)
code = code.replace(
    'box(parts, f"{prefix}_WingR", (850, 1300, 62), (2050, y, z + 35), material, 18, rotation_z=10)',
    'box(parts, f"{prefix}_WingR", (850, 1300, 88), (2050, y, z + 35), material, 18, rotation_z=10, rotation_y=-12)',
)
code = code.replace(
    'box(parts, f"{prefix}_Feature", (1700, 620, 42), (0, y, z + 62), "CA_MW_TrainAAccent", 12)',
    'box(parts, f"{prefix}_Feature", (1700, 620, 55), (0, y, z + 105), "CA_MW_TrainAAccent", 12, rotation_y=-12)',
)
exec(compile(code, str(base) + "::v003", "exec"), globals(), globals())
