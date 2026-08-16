"""Build the second reusable exterior-detail pass for Cairnwell press trains."""

import bpy
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT = ROOT / "SourceAssets/PressTrains/Shared/ExteriorDetail_v002"
FBX = OUT / "FBX"
OUT.mkdir(parents=True, exist_ok=True)
FBX.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.length_unit = "MILLIMETERS"
scene.unit_settings.scale_length = 1.0


PALETTE = {
    "CA_MW_FoundryCharcoal": ((0.016, 0.021, 0.023, 1), 0.35, 0.58),
    "CA_MW_CairnwellGreen": ((0.018, 0.120, 0.090, 1), 0.22, 0.54),
    "CA_MW_SafetyYellow": ((0.78, 0.43, 0.008, 1), 0.18, 0.53),
    "CA_MW_ServiceGrey": ((0.10, 0.13, 0.14, 1), 0.42, 0.60),
    "CA_MW_WorkedSteel": ((0.12, 0.15, 0.16, 1), 0.85, 0.46),
    "CA_MW_DarkRubber": ((0.008, 0.010, 0.010, 1), 0.02, 0.82),
    "CA_MW_TrainAAccent": ((0.035, 0.190, 0.420, 1), 0.20, 0.52),
    "CA_MW_InspectionGlass": ((0.020, 0.100, 0.110, 1), 0.10, 0.30),
    "CA_MW_StateGreen": ((0.008, 0.32, 0.055, 1), 0.04, 0.30),
    "CA_MW_LabelWhite": ((0.55, 0.62, 0.60, 1), 0.12, 0.42),
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


def cylinder(parts, name, diameter, depth, loc, material, axis="Z", vertices=20):
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
    local_bounds = []
    for corner in obj.bound_box:
        local_bounds.append([round(value * 1000, 3) for value in corner])
    minimum = [min(row[index] for row in local_bounds) for index in range(3)]
    maximum = [max(row[index] for row in local_bounds) for index in range(3)]
    path = FBX / f"{name}.fbx"
    bpy.ops.export_scene.fbx(
        filepath=str(path), use_selection=True, apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL", axis_forward="-Y", axis_up="Z",
        use_mesh_modifiers=True, add_leaf_bones=False,
    )
    row = {
        "asset": name, "file": str(path.relative_to(OUT)).replace("\\", "/"),
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper(),
        "measured_dimensions_mm": [round(value * 1000, 3) for value in obj.dimensions],
        "local_aabb_mm": {"min": minimum, "max": maximum},
        "planning_envelope_mm": envelope, "role": role, "pivot": pivot,
        "collision_role": "no_collision_presentation",
        "material_slots": [slot.material.name for slot in obj.material_slots],
        "notes": notes,
    }
    bpy.data.objects.remove(obj, do_unlink=True)
    return row


assets = []

# Crown-centred pack.  The Unreal assembly supplies the stage-specific crown Z,
# so one asset serves S02-S06 without stretching or duplicating geometry.
parts = []
box(parts, "CrownBackplate", (320, 4200, 1800), (2930, 0, 0), "CA_MW_FoundryCharcoal", 45)
box(parts, "MainDriveHousing", (620, 1550, 920), (3130, 0, 180), "CA_MW_CairnwellGreen", 65)
cylinder(parts, "ServoMotor", 690, 1180, (3120, -1250, 260), "CA_MW_ServiceGrey", axis="Y", vertices=28)
cylinder(parts, "ServoShaft", 240, 1510, (3120, -1250, 260), "CA_MW_WorkedSteel", axis="Y", vertices=24)
for y in (1180, 1600):
    cylinder(parts, f"Accumulator_{y}", 360, 1150, (3140, y, 0), "CA_MW_ServiceGrey", vertices=24)
    box(parts, f"AccumulatorBracket_{y}", (420, 520, 180), (2940, y, -480), "CA_MW_FoundryCharcoal", 20)
for y in (-1850, -1450, -1050, -650, -250, 250, 650, 1050, 1450, 1850):
    box(parts, f"CrownLouvre_{y}", (145, 250, 55), (3260, y, -440), "CA_MW_WorkedSteel", 6)
for y in (-1850, -900, 0, 900, 1850):
    for z in (-760, 760):
        cylinder(parts, f"CrownBolt_{y}_{z}", 74, 105, (3290, y, z), "CA_MW_WorkedSteel", axis="X", vertices=12)
for y in (-1850, 1850):
    box(parts, f"CrownLiftLug_{y}", (420, 240, 440), (3060, y, 1110), "CA_MW_SafetyYellow", 30)
box(parts, "CrownAccentBand", (120, 3600, 220), (3280, 0, 700), "CA_MW_TrainAAccent", 14)
box(parts, "CrownDataPlate", (130, 1050, 170), (3310, 0, 410), "CA_MW_LabelWhite", 10)
assets.append(finish(
    "SM_CA_MW_PT_CrownDriveDress_v002", parts, "fixed_crown_drive_release_detail",
    [1100, 4500, 2600], "stage crown centre; source +X operator/CCTV face",
    "Servo/motor housing, accumulators, louvers, lift lugs, bolts and Train A crown identity band.",
))

# Floor-centred hinged service doors and ventilation pack.
parts = []
for index, (y, z) in enumerate(((-1450, 1650), (0, 1650), (1450, 1650)), start=1):
    box(parts, f"ServiceDoor_{index}", (260, 1180, 2450), (3090, y, z), "CA_MW_CairnwellGreen", 34)
    box(parts, f"DoorInset_{index}", (95, 960, 1960), (3265, y, z), "CA_MW_ServiceGrey", 22)
    box(parts, f"DoorHandle_{index}", (160, 85, 420), (3360, y + 390, z), "CA_MW_SafetyYellow", 15)
    for local_y in (-420, -210, 0, 210, 420):
        box(parts, f"DoorVent_{index}_{local_y}", (105, 150, 46), (3335, y + local_y, z + 650), "CA_MW_FoundryCharcoal", 5)
    for local_y in (-500, 500):
        for local_z in (-1050, 1050):
            cylinder(parts, f"DoorBolt_{index}_{local_y}_{local_z}", 65, 110, (3380, y + local_y, z + local_z), "CA_MW_WorkedSteel", axis="X", vertices=12)
box(parts, "DoorHeader", (320, 4250, 310), (3100, 0, 3110), "CA_MW_FoundryCharcoal", 28)
box(parts, "DoorHeaderAccent", (130, 3650, 120), (3350, 0, 3130), "CA_MW_TrainAAccent", 12)
assets.append(finish(
    "SM_CA_MW_PT_ServiceDoorVentPack_v002", parts, "fixed_operator_side_service_door_vent_detail",
    [900, 4500, 3500], "stage local floor centre; source +X operator/CCTV face",
    "Three fabricated hinged doors with inset panels, vents, handles, fasteners and identity header.",
))

# Selectively instanced maintenance platform and ladder; it is intentionally not
# repeated on every stage.
parts = []
box(parts, "AccessDeck", (660, 3600, 180), (3170, 0, 4150), "CA_MW_WorkedSteel", 24)
for y in (-1700, -850, 0, 850, 1700):
    box(parts, f"DeckBracket_{y}", (720, 150, 520), (2920, y, 3900), "CA_MW_FoundryCharcoal", 22)
for y in (-1750, -875, 0, 875, 1750):
    box(parts, f"RailPost_{y}", (105, 105, 1150), (3420, y, 4770), "CA_MW_SafetyYellow", 10)
for z in (4520, 5000, 5280):
    box(parts, f"RailHorizontal_{z}", (110, 3600, 95), (3420, 0, z), "CA_MW_SafetyYellow", 9)
for y in (-1650, -1450):
    box(parts, f"LadderRail_{y}", (120, 120, 4050), (3380, y, 2050), "CA_MW_SafetyYellow", 10)
for z in range(350, 4051, 300):
    box(parts, f"LadderRung_{z}", (130, 320, 70), (3380, -1550, z), "CA_MW_WorkedSteel", 7)
box(parts, "PlatformGate", (110, 520, 1050), (3420, -1450, 4750), "CA_MW_CairnwellGreen", 18)
assets.append(finish(
    "SM_CA_MW_PT_AccessPlatformLadder_v002", parts, "fixed_selective_maintenance_access",
    [1000, 4000, 5500], "stage local floor centre; source +X operator/CCTV face",
    "Selective anti-slip maintenance deck, structural brackets, three-rail edge protection, ladder and access gate.",
))

# S01 gets a more legible automated blank-feed story.
parts = []
box(parts, "BlankPallet", (3600, 3000, 260), (0, -1650, 420), "CA_MW_FoundryCharcoal", 35)
for layer in range(7):
    box(parts, f"BlankLayer_{layer}", (3350, 2750, 55), (0, -1650, 590 + layer * 62), "CA_MW_WorkedSteel", 6)
for x in (-1550, 1550):
    for y in (-2850, -450):
        cylinder(parts, f"CenteringFinger_{x}_{y}", 155, 720, (x, y, 1160), "CA_MW_SafetyYellow", vertices=18)
box(parts, "VacuumTraverse", (5200, 520, 420), (0, -500, 3650), "CA_MW_ServiceGrey", 42)
for x in (-1900, -950, 0, 950, 1900):
    cylinder(parts, f"VacuumDrop_{x}", 105, 1850, (x, -500, 2550), "CA_MW_DarkRubber", vertices=16)
    cylinder(parts, f"VacuumCup_{x}", 330, 160, (x, -500, 1580), "CA_MW_DarkRubber", vertices=22)
box(parts, "SensorMast", (360, 620, 3350), (3050, -1650, 1900), "CA_MW_CairnwellGreen", 38)
box(parts, "SensorHead", (680, 940, 420), (3050, -1650, 3620), "CA_MW_TrainAAccent", 32)
for z in (3000, 3300):
    cylinder(parts, f"SensorLens_{z}", 170, 150, (3410, -1650, z), "CA_MW_StateGreen", axis="X", vertices=20)
assets.append(finish(
    "SM_CA_MW_PT_S01FeederDress_v002", parts, "fixed_s01_automated_blank_feed_detail",
    [6500, 7000, 4500], "S01 local floor centre",
    "Visible blank stack, centering fingers, vacuum traverse/cups and camera-side sensor mast.",
))

# S07 output/inspection is deliberately different from the press stages.
parts = []
box(parts, "OutfeedFrame", (5200, 6500, 520), (0, 1700, 620), "CA_MW_FoundryCharcoal", 45)
for y in range(-1200, 4701, 500):
    cylinder(parts, f"OutfeedRoller_{y}", 250, 4700, (0, y, 980), "CA_MW_WorkedSteel", axis="X", vertices=24)
for x in (-2400, 2400):
    box(parts, f"InspectionUpright_{x}", (360, 520, 3100), (x, 850, 2550), "CA_MW_CairnwellGreen", 38)
box(parts, "InspectionBridge", (5200, 620, 480), (0, 850, 4200), "CA_MW_FoundryCharcoal", 45)
for x in (-1800, -900, 0, 900, 1800):
    box(parts, f"InspectionLight_{x}", (480, 180, 170), (x, 520, 3920), "CA_MW_LabelWhite", 14)
box(parts, "VisionHousing", (1300, 760, 620), (0, 850, 4560), "CA_MW_TrainAAccent", 42)
for x in (-360, 0, 360):
    cylinder(parts, f"VisionLens_{x}", 210, 170, (x, 430, 4540), "CA_MW_InspectionGlass", axis="Y", vertices=24)
box(parts, "OutputStillageBase", (4800, 2800, 360), (0, 4000, 540), "CA_MW_ServiceGrey", 42)
for x in (-2100, 2100):
    for y in (2800, 5200):
        box(parts, f"StillagePost_{x}_{y}", (240, 240, 2200), (x, y, 1700), "CA_MW_SafetyYellow", 22)
assets.append(finish(
    "SM_CA_MW_PT_S07InspectionStillageDress_v002", parts, "fixed_s07_inspection_output_stillage_detail",
    [9000, 13000, 5200], "S07 local floor centre",
    "Roller outfeed, inspection light/vision bridge and output stillage for finished outer panels.",
))

blend_path = OUT / "CA_MW_PressTrain_ExteriorDetail_v002.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
manifest = {
    "$schema": "cairnwell/source/press-train-exterior-detail-v002/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "authority": "Docs/PRESS_TRAINS_IMPLEMENTATION_AUTHORITY.md; Pro Sheets 04/05",
    "source_blend": blend_path.name,
    "coordinate_system": "+X operator/HMI/CCTV side, -X die-change side, +Y material flow, +Z up; millimetres",
    "world_placement": "TBC_NOT_INVENTED", "assets": assets,
    "promotion_authorized": False, "press_shop_complete": False,
}
(OUT / "PRESS_TRAIN_EXTERIOR_DETAIL_MANIFEST_v002.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps({
    "status": "PASS__PRESS_TRAIN_EXTERIOR_DETAIL_V002_BUILT__SOURCE_AUDIT_AND_UNREAL_GATES_REQUIRED__NOT_PROMOTED",
    "asset_count": len(assets),
    "assets": [{"asset": row["asset"], "dimensions_mm": row["measured_dimensions_mm"]} for row in assets],
}, indent=2))
