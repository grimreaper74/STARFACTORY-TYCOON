"""Build reusable heavy-crown and endpoint material-flow presentation assets."""

import bpy
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT = ROOT / "SourceAssets/PressTrains/Shared/CrownEndpointPresentation_v001"
FBX = OUT / "FBX"
OUT.mkdir(parents=True, exist_ok=True)
FBX.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.length_unit = "MILLIMETERS"
scene.unit_settings.scale_length = 1.0

PALETTE = {
    "CA_MW_FoundryCharcoal": ((0.016, 0.021, 0.023, 1), 0.34, 0.60),
    "CA_MW_CairnwellGreen": ((0.018, 0.120, 0.090, 1), 0.22, 0.55),
    "CA_MW_SafetyYellow": ((0.78, 0.43, 0.008, 1), 0.18, 0.54),
    "CA_MW_ServiceGrey": ((0.10, 0.13, 0.14, 1), 0.42, 0.60),
    "CA_MW_WorkedSteel": ((0.18, 0.21, 0.22, 1), 0.86, 0.40),
    "CA_MW_DarkRubber": ((0.008, 0.010, 0.010, 1), 0.02, 0.84),
    "CA_MW_TrainAAccent": ((0.035, 0.190, 0.420, 1), 0.20, 0.52),
    "CA_MW_InspectionCyan": ((0.015, 0.42, 0.50, 1), 0.08, 0.28),
}
materials = {}
for name, (colour, metallic, roughness) in PALETTE.items():
    material = bpy.data.materials.new(name)
    material.diffuse_color = colour
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = colour
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    materials[name] = material


def box(parts, name, dims, loc, material, bevel=0, rotation_z=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=tuple(value / 1000 for value in loc))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = tuple(value / 1000 for value in dims)
    obj.rotation_euler[2] = math.radians(rotation_z)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(materials[material])
    if bevel:
        modifier = obj.modifiers.new("FabricatedEdge", "BEVEL")
        modifier.width = bevel / 1000
        modifier.segments = 2
    parts.append(obj)
    return obj


def cylinder(parts, name, diameter, depth, loc, material, axis="Z", vertices=24):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=diameter / 2000, depth=depth / 1000,
        location=tuple(value / 1000 for value in loc),
    )
    obj = bpy.context.object
    obj.name = name
    if axis == "X":
        obj.rotation_euler[1] = math.radians(90)
    elif axis == "Y":
        obj.rotation_euler[0] = math.radians(90)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    obj.data.materials.append(materials[material])
    parts.append(obj)
    return obj


def finish(name, parts, role, envelope, pivot, notes):
    bpy.ops.object.select_all(action="DESELECT")
    for part in parts:
        part.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = name
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")
    bounds = [[round(value * 1000, 3) for value in corner] for corner in obj.bound_box]
    minimum = [min(row[index] for row in bounds) for index in range(3)]
    maximum = [max(row[index] for row in bounds) for index in range(3)]
    path = FBX / f"{name}.fbx"
    bpy.ops.export_scene.fbx(
        filepath=str(path), use_selection=True, apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL", axis_forward="-Y", axis_up="Z",
        use_mesh_modifiers=True, add_leaf_bones=False,
    )
    row = {
        "asset": name,
        "file": str(path.relative_to(OUT)).replace("\\", "/"),
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper(),
        "measured_dimensions_mm": [round(value * 1000, 3) for value in obj.dimensions],
        "local_aabb_mm": {"min": minimum, "max": maximum},
        "planning_envelope_mm": envelope,
        "role": role,
        "pivot": pivot,
        "collision_role": "no_collision_presentation",
        "material_slots": [slot.material.name for slot in obj.material_slots],
        "notes": notes,
    }
    bpy.data.objects.remove(obj, do_unlink=True)
    return row


assets = []

# Deep shared press crown: fabricated mass behind the existing camera-side
# crown-drive detail. It adds silhouette and load-bearing hierarchy without
# exposing or pretending to simulate hidden internal mechanisms.
parts = []
box(parts, "CrownCore", (4300, 4100, 1500), (0, 0, 0), "CA_MW_FoundryCharcoal", 80)
box(parts, "CrownTopCap", (4800, 4350, 320), (0, 0, 900), "CA_MW_ServiceGrey", 38)
box(parts, "CrownLowerBeam", (5200, 4200, 460), (0, 0, -980), "CA_MW_CairnwellGreen", 45)
for x in (-2300, 2300):
    box(parts, f"CrownCheek_{x}", (420, 4300, 2250), (x, 0, -40), "CA_MW_FoundryCharcoal", 50)
    box(parts, f"CrownCheekWear_{x}", (135, 3500, 1450), (x + (230 if x > 0 else -230), 0, -70), "CA_MW_CairnwellGreen", 24)
for y in (-1800, -900, 0, 900, 1800):
    box(parts, f"CrownRib_{y}", (5000, 180, 2050), (0, y, -80), "CA_MW_ServiceGrey", 20)
for y in (-1750, -875, 0, 875, 1750):
    for z in (-760, 710):
        cylinder(parts, f"CrownFastener_{y}_{z}", 92, 120, (2465, y, z), "CA_MW_WorkedSteel", axis="X", vertices=16)
box(parts, "OperatorDrivePlinth", (520, 2600, 1220), (2670, 0, 40), "CA_MW_CairnwellGreen", 55)
cylinder(parts, "OperatorFlywheelGuard", 1120, 420, (2930, -720, 120), "CA_MW_ServiceGrey", axis="X", vertices=32)
box(parts, "OperatorVentBank", (210, 1050, 620), (2980, 720, 20), "CA_MW_FoundryCharcoal", 22)
for y in (300, 510, 720, 930, 1140):
    box(parts, f"DriveVent_{y}", (105, 160, 460), (3100, y, 20), "CA_MW_WorkedSteel", 6)
box(parts, "TrainAIdentityBand", (125, 3550, 190), (3140, 0, 690), "CA_MW_TrainAAccent", 12)
assets.append(finish(
    "SM_CA_MW_PT_HeavyCrownMass_v001", parts,
    "fixed_shared_heavy_press_crown_presentation", [6500, 5000, 2800],
    "stage crown centre; source +X operator/CCTV face",
    "Deep fabricated crown, structural cheeks/ribs, bolting, guarded drive mass and Train A identity band.",
))

# S01: blank stack, raised top blank and short entry conveyor. Source +Y is
# intentionally upstream so the existing 180-degree assembly yaw presents it
# on the S01 outer endpoint while remaining within the verified stage envelope.
parts = []
box(parts, "BlankStackPallet", (4700, 2500, 260), (0, 1950, 330), "CA_MW_FoundryCharcoal", 32)
for layer in range(10):
    box(parts, f"BlankStackLayer_{layer}", (4420, 2250, 42), (0, 1950, 500 + layer * 48), "CA_MW_WorkedSteel", 5)
for x in (-2050, 2050):
    for y in (900, 3000):
        cylinder(parts, f"BlankGuide_{x}_{y}", 150, 900, (x, y, 1080), "CA_MW_SafetyYellow", vertices=18)
box(parts, "FeedBed", (5000, 2400, 320), (0, 420, 720), "CA_MW_ServiceGrey", 36)
for y in (-520, -180, 160, 500, 840, 1180):
    cylinder(parts, f"FeedRoller_{y}", 170, 4550, (0, y, 960), "CA_MW_WorkedSteel", axis="X", vertices=22)
box(parts, "EnteringBlank", (4520, 1650, 58), (0, 250, 1120), "CA_MW_WorkedSteel", 7)
box(parts, "RaisedTopBlank", (4420, 2250, 58), (0, 1950, 1220), "CA_MW_WorkedSteel", 7)
for x in (-1600, -800, 0, 800, 1600):
    cylinder(parts, f"LiftCup_{x}", 250, 180, (x, 1950, 1360), "CA_MW_DarkRubber", vertices=20)
box(parts, "FeedWitnessBand", (135, 4000, 160), (2460, 1100, 920), "CA_MW_TrainAAccent", 12)
assets.append(finish(
    "SM_CA_MW_PT_S01VisibleBlankFeed_v001", parts,
    "fixed_s01_camera_visible_blank_feed", [6500, 6500, 1800],
    "S01 local floor centre; source +Y upstream before assembly rotation",
    "Packaged blank stack presentation, centering guides, rollers, raised top blank and one blank visibly entering the enclosure.",
))

# S07: a formed outer-panel silhouette leaves the enclosure and a small nested
# stack waits in the stillage. This is presentation geometry for camera proof,
# not an exhaustive forming or robot simulation.
parts = []
box(parts, "DischargeBed", (5200, 5700, 300), (0, -3050, 650), "CA_MW_FoundryCharcoal", 38)
for y in (-500, -950, -1400, -1850, -2300, -2750, -3200, -3650, -4100, -4550, -5000, -5450):
    cylinder(parts, f"DischargeRoller_{y}", 180, 4700, (0, y, 900), "CA_MW_WorkedSteel", axis="X", vertices=22)


def panel(parts, prefix, y, z, material):
    box(parts, f"{prefix}_Centre", (3500, 1450, 62), (0, y, z), material, 18)
    box(parts, f"{prefix}_WingL", (850, 1300, 62), (-2050, y, z + 35), material, 18, rotation_z=-10)
    box(parts, f"{prefix}_WingR", (850, 1300, 62), (2050, y, z + 35), material, 18, rotation_z=10)
    box(parts, f"{prefix}_Feature", (1700, 620, 42), (0, y, z + 62), "CA_MW_TrainAAccent", 12)


panel(parts, "LivePanel", -1650, 1110, "CA_MW_WorkedSteel")
for index, (y, z) in enumerate(((-4650, 1120), (-4750, 1210), (-4850, 1300)), start=1):
    panel(parts, f"StillagePanel_{index}", y, z, "CA_MW_ServiceGrey")
for x in (-2450, 2450):
    box(parts, f"InspectionPost_{x}", (260, 320, 2350), (x, -2050, 2100), "CA_MW_CairnwellGreen", 30)
box(parts, "InspectionBridge", (5200, 420, 360), (0, -2050, 3230), "CA_MW_FoundryCharcoal", 36)
for x in (-1750, -875, 0, 875, 1750):
    box(parts, f"InspectionLight_{x}", (500, 130, 110), (x, -2250, 3030), "CA_MW_InspectionCyan", 10)
box(parts, "DischargeWitnessBand", (135, 4400, 160), (2460, -3000, 1120), "CA_MW_TrainAAccent", 12)
assets.append(finish(
    "SM_CA_MW_PT_S07VisiblePanelDischarge_v001", parts,
    "fixed_s07_camera_visible_panel_discharge", [9000, 6500, 3600],
    "S07 local floor centre; source -Y downstream before assembly rotation",
    "One formed outer panel visibly discharging beneath an inspection bridge plus a restrained nested stillage stack.",
))

blend_path = OUT / "CA_MW_PressTrain_CrownEndpointPresentation_v001.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
manifest = {
    "$schema": "cairnwell/source/press-train-crown-endpoint-presentation-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "authority": "Docs/PRESS_TRAINS_IMPLEMENTATION_AUTHORITY.md; Pro Sheets 04/05",
    "source_blend": blend_path.name,
    "coordinate_system": "+X operator/HMI/CCTV side, -X die-change side, +Y material flow, +Z up; millimetres",
    "world_placement": "TBC_NOT_INVENTED",
    "assets": assets,
    "promotion_authorized": False,
    "press_shop_complete": False,
}
(OUT / "PRESS_TRAIN_CROWN_ENDPOINT_PRESENTATION_MANIFEST_v001.json").write_text(
    json.dumps(manifest, indent=2), encoding="utf-8"
)
print(json.dumps({
    "status": "PASS__PRESS_TRAIN_CROWN_ENDPOINT_PRESENTATION_V001_BUILT__SOURCE_AUDIT_AND_UNREAL_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "asset_count": len(assets),
    "assets": [{"asset": row["asset"], "dimensions_mm": row["measured_dimensions_mm"]} for row in assets],
}, indent=2))
