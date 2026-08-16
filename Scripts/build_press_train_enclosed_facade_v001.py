"""Build reusable dimensioned enclosed facades for the seven-stage press family."""

import bpy
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT = ROOT / "SourceAssets/PressTrains/Shared/EnclosedFacade_v001"
FBX = OUT / "FBX"
OUT.mkdir(parents=True, exist_ok=True)
FBX.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.length_unit = "MILLIMETERS"
scene.unit_settings.scale_length = 1.0


PALETTE = {
    "CA_MW_FoundryCharcoal": ((0.014, 0.019, 0.021, 1), 0.42, 0.57),
    "CA_MW_CairnwellGreen": ((0.012, 0.105, 0.076, 1), 0.27, 0.55),
    "CA_MW_SafetyYellow": ((0.82, 0.46, 0.008, 1), 0.18, 0.50),
    "CA_MW_ServiceGrey": ((0.085, 0.105, 0.112, 1), 0.50, 0.58),
    "CA_MW_WorkedSteel": ((0.13, 0.15, 0.16, 1), 0.88, 0.44),
    "CA_MW_InspectionGlass": ((0.008, 0.075, 0.080, 1), 0.08, 0.28),
    "CA_MW_TrainAAccent": ((0.025, 0.16, 0.39, 1), 0.22, 0.49),
    "CA_MW_LabelWhite": ((0.58, 0.64, 0.62, 1), 0.10, 0.40),
    "CA_MW_DarkRubber": ((0.006, 0.008, 0.009, 1), 0.02, 0.84),
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


def box(parts, name, dims, loc, material, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=tuple(value / 1000 for value in loc))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = tuple(value / 1000 for value in dims)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(materials[material])
    if bevel:
        modifier = obj.modifiers.new("FabricatedEdge", "BEVEL")
        modifier.width = bevel / 1000
        modifier.segments = 2
    parts.append(obj)
    return obj


def cylinder(parts, name, diameter, depth, loc, material, axis="Z", vertices=18):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=diameter / 2000, depth=depth / 1000,
        location=tuple(value / 1000 for value in loc))
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


def facade_fasteners(parts, prefix, x, half_y, z_values):
    for y in (-half_y, half_y):
        for z in z_values:
            cylinder(parts, f"{prefix}_Bolt_{y}_{z}", 68, 105, (x, y, z), "CA_MW_WorkedSteel", axis="X", vertices=12)


def service_door(parts, prefix, x, y, z, width=1120, height=2150):
    box(parts, f"{prefix}_Door", (220, width, height), (x, y, z), "CA_MW_CairnwellGreen", 28)
    box(parts, f"{prefix}_Inset", (90, width - 170, height - 180), (x + 145, y, z), "CA_MW_ServiceGrey", 18)
    box(parts, f"{prefix}_Handle", (145, 70, 370), (x + 230, y + width * 0.31, z), "CA_MW_SafetyYellow", 12)
    for dy in (-300, -150, 0, 150, 300):
        box(parts, f"{prefix}_Vent_{dy}", (85, 115, 38), (x + 225, y + dy, z + height * 0.30), "CA_MW_FoundryCharcoal", 4)


def finish(name, parts, role, planning_envelope, notes):
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
    points = [[round(value * 1000, 3) for value in corner] for corner in obj.bound_box]
    minimum = [min(row[index] for row in points) for index in range(3)]
    maximum = [max(row[index] for row in points) for index in range(3)]
    path = FBX / f"{name}.fbx"
    bpy.ops.export_scene.fbx(
        filepath=str(path), use_selection=True, apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL", axis_forward="-Y", axis_up="Z",
        use_mesh_modifiers=True, add_leaf_bones=False)
    record = {
        "asset": name, "file": str(path.relative_to(OUT)).replace("\\", "/"),
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper(),
        "measured_dimensions_mm": [round(value * 1000, 3) for value in obj.dimensions],
        "local_aabb_mm": {"min": minimum, "max": maximum},
        "planning_envelope_mm": planning_envelope, "role": role,
        "pivot": "stage local floor centre",
        "collision_role": "no_collision_presentation_until_release_gate",
        "material_slots": [slot.material.name for slot in obj.material_slots],
        "notes": notes,
    }
    bpy.data.objects.remove(obj, do_unlink=True)
    return record


assets = []

# Shared S03-S06 enclosure.  The centre process aperture remains visible while
# the surrounding fabricated mass, doors and roof services read as an enclosed press.
parts = []
for y in (-2550, 2550):
    box(parts, f"MidSideTower_{y}", (620, 760, 7600), (3050, y, 4000), "CA_MW_FoundryCharcoal", 55)
    box(parts, f"MidTowerInset_{y}", (180, 520, 6500), (3400, y, 3950), "CA_MW_CairnwellGreen", 28)
box(parts, "MidCrownHeader", (600, 4500, 1250), (3060, 0, 7275), "CA_MW_ServiceGrey", 60)
box(parts, "MidHeaderGreen", (190, 3750, 520), (3400, 0, 7440), "CA_MW_CairnwellGreen", 28)
box(parts, "MidAccentBand", (110, 3650, 155), (3510, 0, 7040), "CA_MW_TrainAAccent", 10)
box(parts, "MidLowerGuard", (500, 4500, 1050), (3070, 0, 720), "CA_MW_FoundryCharcoal", 45)
for y in (-1680, -560, 560, 1680):
    box(parts, f"MidGuardPanel_{y}", (180, 980, 760), (3400, y, 720), "CA_MW_CairnwellGreen", 22)
service_door(parts, "MidDoorL", 3370, -1820, 2000, 980, 1900)
service_door(parts, "MidDoorR", 3370, 1820, 2000, 980, 1900)
for y in (-1280, 0, 1280):
    box(parts, f"MidInspectionFrame_{y}", (210, 980, 1500), (3370, y, 4100), "CA_MW_ServiceGrey", 24)
    box(parts, f"MidInspectionGlass_{y}", (85, 760, 1260), (3510, y, 4100), "CA_MW_InspectionGlass", 16)
box(parts, "MidIdentityPlate", (135, 1500, 270), (3515, -850, 6300), "CA_MW_LabelWhite", 16)
box(parts, "MidHMIPlate", (150, 620, 720), (3520, 1840, 3020), "CA_MW_TrainAAccent", 22)
for y in (-1650, 0, 1650):
    box(parts, f"MidRoofPod_{y}", (720, 920, 520), (3000, y, 8170), "CA_MW_CairnwellGreen", 40)
    cylinder(parts, f"MidRoofFan_{y}", 420, 150, (3400, y, 8170), "CA_MW_WorkedSteel", axis="X", vertices=24)
facade_fasteners(parts, "Mid", 3515, 2880, (420, 1850, 3550, 5900, 7900))
assets.append(finish(
    "SM_CA_MW_PT_MidPressEnclosedFacade_v001", parts, "fixed_s03_s06_enclosed_operator_facade",
    [6500, 6500, 8500],
    "Shared form/trim/pierce/flange facade with enclosed mass, inspection glazing, access doors, lower guards, HMI and roof service pods. Source +X is CCTV/operator side."))

# S02 draw press uses a taller, heavier crown and a wider guarded aperture.
parts = []
for y in (-2850, 2850):
    box(parts, f"DrawTower_{y}", (700, 720, 10100), (3200, y, 5200), "CA_MW_FoundryCharcoal", 60)
    box(parts, f"DrawTowerGreen_{y}", (190, 480, 8900), (3590, y, 5100), "CA_MW_CairnwellGreen", 28)
box(parts, "DrawCrownHeader", (680, 5200, 1700), (3210, 0, 9350), "CA_MW_ServiceGrey", 70)
box(parts, "DrawCrownInset", (190, 4450, 720), (3590, 0, 9550), "CA_MW_CairnwellGreen", 34)
box(parts, "DrawAccentBand", (115, 4250, 180), (3700, 0, 9010), "CA_MW_TrainAAccent", 12)
box(parts, "DrawLowerGuard", (540, 5100, 1200), (3220, 0, 760), "CA_MW_FoundryCharcoal", 50)
for y in (-2050, -680, 680, 2050):
    box(parts, f"DrawGuardPanel_{y}", (190, 1180, 880), (3600, y, 760), "CA_MW_CairnwellGreen", 24)
service_door(parts, "DrawDoorL", 3560, -2200, 2300, 1100, 2200)
service_door(parts, "DrawDoorR", 3560, 2200, 2300, 1100, 2200)
for y in (-1450, 0, 1450):
    box(parts, f"DrawWindowFrame_{y}", (230, 1180, 1800), (3560, y, 4850), "CA_MW_ServiceGrey", 28)
    box(parts, f"DrawWindow_{y}", (85, 900, 1500), (3715, y, 4850), "CA_MW_InspectionGlass", 18)
box(parts, "DrawIdentityPlate", (140, 1750, 310), (3720, -950, 7900), "CA_MW_LabelWhite", 18)
box(parts, "DrawHMIPlate", (150, 700, 820), (3720, 2180, 3400), "CA_MW_TrainAAccent", 24)
for y in (-1950, -650, 650, 1950):
    box(parts, f"DrawRoofPod_{y}", (760, 900, 560), (3160, y, 10650), "CA_MW_CairnwellGreen", 42)
facade_fasteners(parts, "Draw", 3720, 3180, (450, 2200, 4300, 6800, 9900))
assets.append(finish(
    "SM_CA_MW_PT_DrawPressEnclosedFacade_v001", parts, "fixed_s02_heavy_draw_press_enclosed_operator_facade",
    [7000, 7000, 11000],
    "Taller draw-press facade with heavy crown, guarded aperture, doors, glazing, HMI, roof pods and physical ID plate."))

# S01 automated destack/load cell: visibly enclosed but differentiated from press frames.
parts = []
for y in (-2600, 2600):
    box(parts, f"FeedCorner_{y}", (620, 620, 5850), (2900, y, 3075), "CA_MW_FoundryCharcoal", 52)
box(parts, "FeedHeader", (620, 4800, 1050), (2900, 0, 5425), "CA_MW_ServiceGrey", 55)
box(parts, "FeedHeaderGreen", (180, 4050, 430), (3255, 0, 5550), "CA_MW_CairnwellGreen", 26)
box(parts, "FeedLowerPlinth", (520, 4800, 950), (2920, 0, 620), "CA_MW_FoundryCharcoal", 45)
for y in (-1700, -570, 570, 1700):
    box(parts, f"FeedLowerPanel_{y}", (170, 960, 680), (3270, y, 620), "CA_MW_CairnwellGreen", 20)
for y in (-1450, 0, 1450):
    box(parts, f"FeedVisionFrame_{y}", (220, 1120, 1850), (3260, y, 3250), "CA_MW_ServiceGrey", 26)
    box(parts, f"FeedVisionGlass_{y}", (82, 900, 1600), (3400, y, 3250), "CA_MW_InspectionGlass", 16)
service_door(parts, "FeedServiceDoor", 3250, 2050, 2150, 900, 2050)
box(parts, "FeedIdentityPlate", (140, 1800, 300), (3415, -900, 4850), "CA_MW_LabelWhite", 17)
box(parts, "FeedHMIPlate", (145, 660, 780), (3415, 2100, 3720), "CA_MW_TrainAAccent", 22)
for y in (-1800, -900, 0, 900, 1800):
    box(parts, f"FeedRoofRib_{y}", (740, 120, 470), (2880, y, 6180), "CA_MW_SafetyYellow", 12)
facade_fasteners(parts, "Feed", 3410, 2880, (380, 1850, 3600, 5700))
assets.append(finish(
    "SM_CA_MW_PT_S01DestackEnclosedFacade_v001", parts, "fixed_s01_destack_load_enclosed_operator_facade",
    [6500, 6500, 6500],
    "Automated blank-load enclosure with vision glazing, access door, HMI, roof ribs and distinct lower panels."))

# S07 unload/inspect cell: wider vision enclosure and outfeed identity.
parts = []
for y in (-3200, 3200):
    box(parts, f"UnloadCorner_{y}", (650, 680, 6200), (4050, y, 3300), "CA_MW_FoundryCharcoal", 55)
box(parts, "UnloadHeader", (650, 5900, 1100), (4050, 0, 5850), "CA_MW_ServiceGrey", 58)
box(parts, "UnloadHeaderGreen", (190, 5000, 450), (4420, 0, 5960), "CA_MW_CairnwellGreen", 28)
box(parts, "UnloadLowerGuard", (540, 5900, 980), (4070, 0, 650), "CA_MW_FoundryCharcoal", 46)
for y in (-2200, -1100, 0, 1100, 2200):
    box(parts, f"UnloadGuardPanel_{y}", (175, 950, 700), (4430, y, 650), "CA_MW_CairnwellGreen", 22)
for y in (-2100, -1050, 0, 1050, 2100):
    box(parts, f"UnloadVisionFrame_{y}", (220, 880, 2300), (4420, y, 3450), "CA_MW_ServiceGrey", 26)
    box(parts, f"UnloadVisionGlass_{y}", (82, 680, 2050), (4560, y, 3450), "CA_MW_InspectionGlass", 16)
service_door(parts, "UnloadServiceDoor", 4410, 2700, 2100, 820, 1950)
box(parts, "UnloadIdentityPlate", (140, 1900, 300), (4575, -1000, 5300), "CA_MW_LabelWhite", 17)
box(parts, "UnloadHMIPlate", (145, 720, 820), (4575, 2750, 4000), "CA_MW_TrainAAccent", 24)
for y in (-2400, -1200, 0, 1200, 2400):
    cylinder(parts, f"UnloadRoofBeacon_{y}", 240, 300, (4050, y, 6670), "CA_MW_SafetyYellow", vertices=18)
facade_fasteners(parts, "Unload", 4570, 3500, (380, 1900, 4100, 6100))
assets.append(finish(
    "SM_CA_MW_PT_S07UnloadInspectEnclosedFacade_v001", parts, "fixed_s07_unload_inspect_enclosed_operator_facade",
    [9000, 7500, 7000],
    "Wide inspection glazing, guarded outfeed base, service access, HMI and physical ID panel differentiate the automated endpoint."))

blend_path = OUT / "CA_MW_PressTrain_EnclosedFacade_v001.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
manifest = {
    "$schema": "cairnwell/source/press-train-enclosed-facade-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "authority": "Docs/PRESS_TRAINS_IMPLEMENTATION_AUTHORITY.md; Pro Sheets 04/05",
    "source_blend": blend_path.name,
    "coordinate_system": "+X operator/HMI/CCTV facade, -X die-change side, +Y material flow, +Z up; millimetres",
    "design_model": "CCTV-first enclosed machinery; exterior, limited visible motion, sheet flow, lighting and sound sell operation",
    "world_placement": "TBC_NOT_INVENTED", "assets": assets,
    "promotion_authorized": False, "press_shop_complete": False,
}
(OUT / "PRESS_TRAIN_ENCLOSED_FACADE_MANIFEST_v001.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps({
    "status": "PASS__PRESS_TRAIN_ENCLOSED_FACADE_V001_BUILT__SOURCE_AUDIT_AND_UNREAL_GATES_REQUIRED__NOT_PROMOTED",
    "asset_count": len(assets),
    "assets": [{"asset": row["asset"], "dimensions_mm": row["measured_dimensions_mm"]} for row in assets],
}, indent=2))
