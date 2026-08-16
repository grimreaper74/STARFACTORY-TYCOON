"""Build the dimensioned shared seven-stage press-train source kit at local origin."""

import bpy
import json
import math
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT = ROOT / "SourceAssets/PressTrains/Shared/Blockout_v001"
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
    "CA_MW_ServiceGrey": ((0.19, 0.23, 0.24, 1), 0.45, 0.52),
    "CA_MW_WorkedSteel": ((0.12, 0.15, 0.16, 1), 0.85, 0.46),
    "CA_MW_DarkRubber": ((0.008, 0.010, 0.010, 1), 0.02, 0.82),
    "CA_MW_InspectionGlass": ((0.025, 0.120, 0.130, 0.38), 0.12, 0.22),
    "CA_MW_TrainAAccent": ((0.035, 0.190, 0.420, 1), 0.20, 0.52),
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
    if name == "CA_MW_InspectionGlass":
        bsdf.inputs["Alpha"].default_value = colour[3]
        material.surface_render_method = "DITHERED"
    materials[name] = material


assets = {}


def box(name, dims, loc, material, bevel=0):
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
    return obj


def cylinder(name, diameter, depth, loc, material, axis="Z", vertices=20):
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
    return obj


def add_fasteners(parts, prefix, xs, ys, zs, diameter=52, depth=36, axis="Y"):
    for index, (x, y, z) in enumerate((x, y, z) for x in xs for y in ys for z in zs):
        parts.append(cylinder(f"{prefix}_Fastener_{index:02d}", diameter, depth, (x, y, z), "CA_MW_WorkedSteel", axis=axis, vertices=12))


def join_asset(name, parts, role, envelope_mm, pivot, collision_role, notes):
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
    assets[name] = {
        "object": obj,
        "role": role,
        "planning_envelope_mm": envelope_mm,
        "pivot": pivot,
        "collision_role": collision_role,
        "notes": notes,
    }


def enclosure_panels(parts, prefix, width, length, height, accent=False):
    half_x = width / 2
    half_y = length / 2
    # Four fabricated corner towers and top/bottom structure establish a truthful shell.
    for x in (-half_x + 360, half_x - 360):
        for y in (-half_y + 360, half_y - 360):
            parts.append(box(f"{prefix}_Column_{x}_{y}", (720, 720, height - 500), (x, y, (height - 500) / 2), "CA_MW_FoundryCharcoal", bevel=45))
    parts.extend([
        box(f"{prefix}_Base", (width, length, 360), (0, 0, 180), "CA_MW_FoundryCharcoal", bevel=35),
        box(f"{prefix}_Roof", (width, length, 500), (0, 0, height - 250), "CA_MW_FoundryCharcoal", bevel=50),
        box(f"{prefix}_UpperHousing", (width - 900, length - 900, 1650), (0, 0, height - 1325), "CA_MW_CairnwellGreen", bevel=70),
    ])
    # Side service panels, glazing and proper yellow access edges.
    for side, sign in (("L", -1), ("R", 1)):
        panel_x = sign * (half_x - 130)
        door_x = sign * (half_x - 145)
        window_x = sign * (half_x - 19)
        edge_x = sign * (half_x - 55)
        parts.append(box(f"{prefix}_SidePanel_{side}", (260, length - 1600, height * 0.48), (panel_x, 0, height * 0.39), "CA_MW_ServiceGrey", bevel=24))
        parts.append(box(f"{prefix}_ServiceDoor_{side}", (290, 1500, 2350), (door_x, -900, 1450), "CA_MW_CairnwellGreen", bevel=24))
        parts.append(box(f"{prefix}_DoorWindow_{side}", (38, 900, 700), (window_x, -900, 1850), "CA_MW_InspectionGlass", bevel=18))
        parts.append(box(f"{prefix}_DoorEdge_{side}", (110, 1700, 120), (edge_x, -900, 2580), "CA_MW_SafetyYellow", bevel=12))
    # Front and rear camera portals preserve deliberate internal glimpses.
    for end, y in (("In", -half_y + 180), ("Out", half_y - 180)):
        parts.append(box(f"{prefix}_{end}_LowerGuard", (width - 1500, 260, 1050), (0, y, 900), "CA_MW_FoundryCharcoal", bevel=22))
        view_y = (-half_y + 21) if end == "In" else (half_y - 21)
        parts.append(box(f"{prefix}_{end}_View", (width - 2300, 42, 1550), (0, view_y, 2450), "CA_MW_InspectionGlass", bevel=18))
        parts.append(box(f"{prefix}_{end}_Lintel", (width - 1200, 360, 420), (0, y, 3500), "CA_MW_CairnwellGreen", bevel=28))
    # Supported roof services and access hatches add readable industrial density.
    for x in (-width * 0.28, 0, width * 0.28):
        parts.append(box(f"{prefix}_RoofDrive_{x}", (700, 1100, 520), (x, 0, height - 260), "CA_MW_ServiceGrey", bevel=45))
        parts.append(cylinder(f"{prefix}_RoofRoute_{x}", 120, length - 1200, (x, 0, height - 520), "CA_MW_SafetyYellow", axis="Y"))
    for y in (-length * 0.25, 0, length * 0.25):
        parts.append(box(f"{prefix}_AccessHatch_{y}", (width - 1700, 55, 820), (0, y, height - 1750), "CA_MW_FoundryCharcoal", bevel=18))
        add_fasteners(parts, f"{prefix}_Hatch_{y}", (-width * 0.32, width * 0.32), (y - 36,), (height - 2050, height - 1450), axis="Y")
    if accent:
        parts.append(box(f"{prefix}_TrainAccent", (width - 1800, 85, 360), (0, -half_y + 42.5, height - 1370), "CA_MW_TrainAAccent", bevel=16))


# Exact full-train installation platform and two service corridors.
parts = [
    box("TrainPlatform", (15000, 56000, 350), (0, 22500, 175), "CA_MW_FoundryCharcoal", bevel=70),
    box("OperatorWalkway", (1500, 55000, 120), (-6750, 22500, 410), "CA_MW_ServiceGrey", bevel=25),
    box("DieChangeCorridor", (2500, 55000, 120), (6250, 22500, 410), "CA_MW_ServiceGrey", bevel=25),
]
for y in range(-4500, 50001, 7500):
    parts.append(box(f"StageDatum_{y}", (14500, 90, 30), (0, y, 430), "CA_MW_SafetyYellow", bevel=8))
join_asset(
    "SM_CA_MW_PT_CommonPlatform_v001", parts, "fixed_train_platform",
    [15000, 56000, 500], "local train origin; +Y flow", "fixed_blocking",
    "Full 56 m shared train footprint with operator and die-change sides")


# Service spine kept as a separate reusable visual/collision module.
parts = [
    box("SpineFrame", (950, 52000, 1150), (0, 22500, 575), "CA_MW_FoundryCharcoal", bevel=50),
]
for x, z, material in ((-250, 900, "CA_MW_SafetyYellow"), (0, 900, "CA_MW_CairnwellGreen"), (250, 900, "CA_MW_ServiceGrey")):
    parts.append(cylinder(f"SpineRoute_{x}", 130, 51000, (x, 22500, z), material, axis="Y"))
for y in range(-2500, 50001, 7500):
    parts.append(box(f"ServiceCabinet_{y}", (820, 900, 1300), (0, y, 1350), "CA_MW_CairnwellGreen", bevel=45))
    parts.append(box(f"ServiceDoor_{y}", (700, 55, 1120), (0, y - 478, 1350), "CA_MW_FoundryCharcoal", bevel=22))
    parts.append(box(f"ServiceHandle_{y}", (55, 70, 260), (250, y - 520, 1350), "CA_MW_SafetyYellow", bevel=10))
join_asset(
    "SM_CA_MW_PT_CommonUtilitySpine_v001", parts, "fixed_utility_spine",
    [1100, 54000, 2100], "local origin; placed on service side", "fixed_detail_blocking",
    "Supported electrical, controls, air and service-cabinet presentation")


# Continuous transfer rail and guarded carriers.
parts = [
    box("LeftRail", (260, 51000, 340), (-650, 22500, 620), "CA_MW_WorkedSteel", bevel=30),
    box("RightRail", (260, 51000, 340), (650, 22500, 620), "CA_MW_WorkedSteel", bevel=30),
]
for y in range(-2500, 48001, 1500):
    parts.append(box(f"RailTie_{y}", (1800, 240, 190), (0, y, 480), "CA_MW_FoundryCharcoal", bevel=18))
join_asset(
    "SM_CA_MW_PT_TransferRail_v001", parts, "fixed_transfer_rail",
    [1800, 52000, 900], "local origin; rail centreline", "fixed_blocking",
    "Shared overhead-servo transfer guide presentation between stages")


# Five reusable press shells. Solid visible geometry stays within planning envelopes.
press_specs = [
    ("Draw", "S02", 7000, 6200, 11000, [7000, 12000, 11000]),
    ("Form", "S03", 6500, 6200, 9500, [6500, 11000, 9500]),
    ("Trim", "S04", 6500, 6200, 9000, [6500, 11000, 9000]),
    ("Pierce", "S05", 6500, 6200, 8500, [6500, 11000, 8500]),
    ("Flange", "S06", 6500, 6200, 9000, [6500, 11000, 9000]),
]
for role, stage, width, length, height, envelope in press_specs:
    parts = []
    enclosure_panels(parts, stage, width, length, height, accent=True)
    # Visible press crown, guides and lower die area behind the deliberate portals.
    parts.append(box(f"{stage}_Crown", (width - 1700, 3200, 1200), (0, 0, height - 2500), "CA_MW_FoundryCharcoal", bevel=70))
    for x in (-width * 0.27, width * 0.27):
        parts.append(box(f"{stage}_SlideGuide_{x}", (420, 3300, height * 0.48), (x, 0, height * 0.44), "CA_MW_WorkedSteel", bevel=28))
    parts.append(box(f"{stage}_LowerDieBed", (width - 1900, 4200, 820), (0, 0, 850), "CA_MW_WorkedSteel", bevel=45))
    if role in ("Trim", "Pierce"):
        parts.append(box(f"{stage}_ScrapChute", (width - 2200, 3500, 620), (0, 700, 420), "CA_MW_ServiceGrey", bevel=38))
    join_asset(
        f"SM_CA_MW_PT_PressFrame_{role}_v001", parts, f"fixed_{role.lower()}_press_shell",
        envelope, "stage local origin at floor centre", "fixed_blocking_shell",
        f"Enclosed {role.lower()} stage with service doors, windows, roof drives and internal silhouette")


# S01 destack/load cell.
parts = []
enclosure_panels(parts, "S01", 6500, 6200, 6500, accent=True)
parts.extend([
    box("S01_LiftWell", (5000, 4300, 450), (0, 0, 520), "CA_MW_WorkedSteel", bevel=35),
    box("S01_GantryBridge", (5400, 700, 800), (0, 0, 5000), "CA_MW_FoundryCharcoal", bevel=45),
    box("S01_CentringBed", (4800, 3800, 450), (0, 700, 1000), "CA_MW_ServiceGrey", bevel=30),
])
for x in (-2100, 2100):
    parts.append(cylinder(f"S01_Fanner_{x}", 420, 1700, (x, -1100, 2200), "CA_MW_SafetyYellow"))
join_asset(
    "SM_CA_MW_PT_DestackLoadCell_v001", parts, "fixed_destack_load_cell",
    [6500, 11000, 6500], "S01 local floor centre", "fixed_blocking_shell",
    "Enclosed blank stack, fanner, centring and guarded load-transfer presentation")


# S07 unload/inspection/stillage cell.
parts = []
enclosure_panels(parts, "S07", 9000, 7000, 7000, accent=True)
parts.extend([
    box("S07_InspectionTunnel", (6200, 3000, 3100), (0, 500, 2800), "CA_MW_FoundryCharcoal", bevel=70),
    box("S07_LightPortal", (5400, 45, 2100), (0, -1020, 2800), "CA_MW_InspectionGlass", bevel=25),
    box("S07_StillageBed", (6000, 3000, 420), (0, 1800, 650), "CA_MW_WorkedSteel", bevel=35),
])
for x in (-3000, 3000):
    parts.append(cylinder(f"S07_RobotPedestal_{x}", 1000, 1000, (x, -1100, 820), "CA_MW_FoundryCharcoal", vertices=28))
    parts.append(box(f"S07_RobotPark_{x}", (900, 900, 900), (x, -1100, 1750), "CA_MW_SafetyYellow", bevel=70))
join_asset(
    "SM_CA_MW_PT_UnloadInspectCell_v001", parts, "fixed_unload_inspection_cell",
    [9000, 13000, 7000], "S07 local floor centre", "fixed_blocking_shell",
    "Dual unload positions, inspection tunnel and stillage presentation")


# Moving presentation modules remain separate and origin-pivoted.
parts = [
    box("RamBody", (5000, 4200, 700), (0, 0, 0), "CA_MW_WorkedSteel", bevel=50),
    box("RamFace", (4600, 3800, 180), (0, 0, -430), "CA_MW_ServiceGrey", bevel=25),
]
join_asset("SM_CA_MW_PT_PressSlide_v001", parts, "moving_press_slide", [5200, 4500, 1000], "origin at slide guide centre", "query_only_mover", "Z stroke 300-800 mm; safe top dead centre")

parts = [
    box("BolsterBody", (5200, 5000, 500), (0, 0, 0), "CA_MW_WorkedSteel", bevel=45),
]
for y in (-1800, -600, 600, 1800):
    parts.append(cylinder(f"BolsterRoll_{y}", 260, 4700, (0, y, 0), "CA_MW_ServiceGrey", axis="X", vertices=20))
join_asset("SM_CA_MW_PT_MovingBolster_v001", parts, "moving_bolster", [5400, 5200, 700], "origin at linear guide centre", "query_only_mover", "Local X travel 0-3500 mm; safe in press")

parts = [
    box("LowerDie", (4800, 3600, 450), (0, 0, -250), "CA_MW_WorkedSteel", bevel=45),
    box("UpperDie", (4400, 3300, 450), (0, 0, 250), "CA_MW_ServiceGrey", bevel=45),
]
for x in (-1900, 1900):
    for y in (-1300, 1300):
        parts.append(cylinder(f"DieGuide_{x}_{y}", 180, 850, (x, y, 0), "CA_MW_SafetyYellow", vertices=18))
join_asset("SM_CA_MW_PT_StageDieSet_v001", parts, "recipe_die_set", [5000, 3800, 1000], "origin at die split plane", "query_only_tooling", "Interchangeable train/stage recipe tooling")

parts = [box("DieCartDeck", (4500, 5500, 620), (0, 0, 0), "CA_MW_FoundryCharcoal", bevel=55)]
for x in (-1750, 1750):
    for y in (-2100, 0, 2100):
        parts.append(cylinder(f"DieCartWheel_{x}_{y}", 520, 240, (x, y, -380), "CA_MW_DarkRubber", axis="X", vertices=24))
join_asset("SM_CA_MW_PT_DieCart_v001", parts, "moving_die_cart", [4800, 6000, 1100], "origin at cart deck centre", "query_only_mover", "Recipe X/Y service motion; parked in service bay")

parts = [
    box("Crossbar", (6200, 300, 350), (0, 0, 0), "CA_MW_FoundryCharcoal", bevel=28),
    box("LeftGripper", (720, 540, 300), (-2200, 0, -250), "CA_MW_SafetyYellow", bevel=35),
    box("RightGripper", (720, 540, 300), (2200, 0, -250), "CA_MW_SafetyYellow", bevel=35),
]
join_asset("SM_CA_MW_PT_TransferCrossbar_v001", parts, "moving_transfer_crossbar", [6500, 800, 800], "origin at crossbar servo centre", "query_only_mover", "Y pitch 0-7500 mm; grippers open safe")

parts = [box("LiftTable", (5000, 5000, 700), (0, 0, 0), "CA_MW_WorkedSteel", bevel=45)]
for x in (-1900, 1900):
    for y in (-1900, 1900):
        parts.append(cylinder(f"LiftGuide_{x}_{y}", 220, 1100, (x, y, -450), "CA_MW_ServiceGrey", vertices=20))
join_asset("SM_CA_MW_PT_DestackLift_v001", parts, "moving_destack_lift", [5300, 5300, 1600], "origin at lower lift position", "query_only_mover", "Z travel 0-1200 mm; safe lowered")


# Export semantic modules and a deterministic source manifest.
exports = []
for name, data in assets.items():
    obj = data["object"]
    path = FBX / f"{name}.fbx"
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(
        filepath=str(path), use_selection=True, apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL", axis_forward="-Y", axis_up="Z",
        use_mesh_modifiers=True, add_leaf_bones=False)
    exports.append({
        "asset": name,
        "file": str(path.relative_to(OUT)).replace("\\", "/"),
        "bytes": path.stat().st_size,
        "measured_dimensions_mm": [round(value * 1000, 3) for value in obj.dimensions],
        "planning_envelope_mm": data["planning_envelope_mm"],
        "role": data["role"],
        "pivot": data["pivot"],
        "collision_role": data["collision_role"],
        "material_slots": [slot.material.name for slot in obj.material_slots],
        "notes": data["notes"],
    })

blend = OUT / "CA_MW_PressTrain_SharedKit_v001.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
manifest = {
    "$schema": "cairnwell/source/press-train-shared-kit-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "source_blend": blend.name,
    "blender_version": bpy.app.version_string,
    "authority": "Docs/PRESS_TRAINS_IMPLEMENTATION_AUTHORITY.md; Pro Sheets 04-08",
    "coordinate_system": "+X across train, +Y material flow, +Z up; millimetres",
    "world_placement": "TBC_NOT_INVENTED",
    "stage_centres_local_y_mm": [0, 7500, 15000, 22500, 30000, 37500, 45000],
    "assets": exports,
    "promotion_authorized": False,
    "press_shop_complete": False,
}
(OUT / "PRESS_TRAIN_SHARED_KIT_MANIFEST_v001.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps({
    "status": "PASS__PRESS_TRAIN_SHARED_SOURCE_V001_BUILT__AUDIT_AND_UNREAL_GATES_REQUIRED__NOT_PROMOTED",
    "asset_count": len(exports),
    "world_placement": "TBC_NOT_INVENTED",
}, indent=2))
