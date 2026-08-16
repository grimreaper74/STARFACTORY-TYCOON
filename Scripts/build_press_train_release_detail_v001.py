"""Build reusable release-detail geometry for Cairnwell press trains.

This kit is deliberately station-local.  It improves the retained Train A v022
presentation without authorising or inventing Train A-D production transforms.
"""

import bpy
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT = ROOT / "SourceAssets/PressTrains/Shared/ReleaseDetail_v001"
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
    "CA_MW_StateGreen": ((0.018, 0.52, 0.18, 1), 0.05, 0.26),
    "CA_MW_StateAmber": ((0.92, 0.35, 0.01, 1), 0.05, 0.28),
    "CA_MW_StateRed": ((0.65, 0.015, 0.008, 1), 0.05, 0.30),
    "CA_MW_StateBlue": ((0.02, 0.28, 0.70, 1), 0.08, 0.30),
    "CA_MW_LabelWhite": ((0.62, 0.69, 0.67, 1), 0.12, 0.42),
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


def pipe_between(parts, name, start, end, diameter, material, vertices=14):
    sx, sy, sz = (value / 1000 for value in start)
    ex, ey, ez = (value / 1000 for value in end)
    dx, dy, dz = ex - sx, ey - sy, ez - sz
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=diameter / 2000, depth=length,
        location=((sx + ex) / 2, (sy + ey) / 2, (sz + ez) / 2),
    )
    obj = bpy.context.object
    obj.name = name
    direction = mathutils.Vector((dx, dy, dz))
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = direction.to_track_quat("Z", "Y")
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    obj.data.materials.append(materials[material])
    parts.append(obj)
    return obj


def torus(parts, name, major_diameter, minor_diameter, loc, material, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_diameter / 2000,
        minor_radius=minor_diameter / 2000,
        major_segments=24, minor_segments=8,
        location=tuple(value / 1000 for value in loc),
        rotation=tuple(math.radians(value) for value in rotation),
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(materials[material])
    parts.append(obj)
    return obj


def finish(name, parts, role, envelope, pivot, collision_role, notes):
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
        "planning_envelope_mm": envelope,
        "role": role,
        "pivot": pivot,
        "collision_role": collision_role,
        "material_slots": [slot.material.name for slot in obj.material_slots],
        "notes": notes,
    }
    bpy.data.objects.remove(obj, do_unlink=True)
    return row


# mathutils is imported after Blender has initialised its Python environment.
import mathutils

assets = []

# Transform-compatible replacement for the original 4500 x 5500 mm die cart.
# The origin remains at deck centre so existing v022 actor transforms are retained.
parts = []
box(parts, "CartDeck", (4500, 5500, 520), (0, 0, 0), "CA_MW_FoundryCharcoal", 65)
box(parts, "UpperWearDeck", (4100, 5100, 105), (0, 0, 310), "CA_MW_WorkedSteel", 24)
for x in (-1650, 1650):
    box(parts, f"CarrierRail_{x}", (260, 4800, 210), (x, 0, 430), "CA_MW_WorkedSteel", 22)
    for y in (-1800, -600, 600, 1800):
        cylinder(parts, f"DeckRoller_{x}_{y}", 220, 330, (x, y, 570), "CA_MW_WorkedSteel", axis="X", vertices=20)
for x in (-1780, 1780):
    for y in (-2050, 0, 2050):
        cylinder(parts, f"Wheel_{x}_{y}", 600, 280, (x, y, -430), "CA_MW_DarkRubber", axis="X", vertices=28)
        cylinder(parts, f"Hub_{x}_{y}", 245, 330, (x, y, -430), "CA_MW_WorkedSteel", axis="X", vertices=20)
    box(parts, f"BogieBeam_{x}", (420, 4650, 330), (x, 0, -300), "CA_MW_ServiceGrey", 35)
for y in (-2150, 2150):
    for x in (-1650, 1650):
        box(parts, f"HydraulicClamp_{x}_{y}", (420, 520, 480), (x, y, 700), "CA_MW_CairnwellGreen", 35)
        cylinder(parts, f"ClampPin_{x}_{y}", 150, 490, (x, y, 930), "CA_MW_SafetyYellow", axis="Z", vertices=18)
box(parts, "DriveHousing", (1120, 900, 760), (0, -2050, -120), "CA_MW_CairnwellGreen", 55)
box(parts, "CableChain", (720, 2200, 260), (0, -1200, -600), "CA_MW_DarkRubber", 25)
torus(parts, "TowEye", 430, 105, (0, 2840, -40), "CA_MW_SafetyYellow", rotation=(90, 0, 0))
for x in (-2070, 2070):
    box(parts, f"HazardBumper_{x}", (180, 5050, 170), (x, 0, 250), "CA_MW_SafetyYellow", 22)
box(parts, "CartIdentityPlate", (70, 3850, 360), (-2285, 0, 90), "CA_MW_TrainAAccent", 15)
box(parts, "CartServicePlate", (78, 1500, 190), (-2330, 0, -150), "CA_MW_LabelWhite", 12)
assets.append(finish(
    "SM_CA_MW_PT_DieCartRelease_v001", parts,
    "moving_die_cart_release_visual", [4800, 6000, 2000],
    "origin at cart deck centre; transform-compatible with SM_CA_MW_PT_DieCart_v003",
    "query_only_mover",
    "Six-wheel bogies, rollers, clamps, drive housing, cable chain, tow eye and Cairnwell family identity plates.",
))

# Separate die/load module permits recipe and service-state variation without
# duplicating the cart base.
parts = []
box(parts, "LowerDieShoe", (3800, 4600, 300), (0, 0, 540), "CA_MW_WorkedSteel", 45)
box(parts, "DieBody", (3200, 3900, 510), (0, 0, 935), "CA_MW_ServiceGrey", 65)
box(parts, "UpperCarrier", (3550, 4300, 230), (0, 0, 1310), "CA_MW_FoundryCharcoal", 38)
for x in (-1420, 1420):
    for y in (-1780, 1780):
        cylinder(parts, f"GuidePost_{x}_{y}", 210, 780, (x, y, 1040), "CA_MW_WorkedSteel", vertices=24)
for x in (-1650, 1650):
    box(parts, f"LiftLug_{x}", (260, 450, 420), (x, 0, 1500), "CA_MW_SafetyYellow", 30)
box(parts, "DieRecipeBand", (3350, 95, 220), (0, -2190, 1020), "CA_MW_TrainAAccent", 14)
assets.append(finish(
    "SM_CA_MW_PT_DieCartToolingLoad_v001", parts,
    "interchangeable_die_cart_tooling_load", [4300, 5000, 1900],
    "origin at cart deck centre; place at same transform as cart",
    "no_collision_presentation",
    "Separate large outer-panel die set with guide posts, lift lugs and Train A recipe band.",
))

# Higher-quality replacement for the v001 fixed die-change dock.
parts = []
box(parts, "DockFoundation", (620, 4550, 520), (-2880, 0, 430), "CA_MW_FoundryCharcoal", 48)
box(parts, "DockWearRail", (220, 4250, 150), (-3200, 0, 760), "CA_MW_WorkedSteel", 20)
for y in (-1700, -570, 570, 1700):
    cylinder(parts, f"DockRoller_{y}", 260, 450, (-3140, y, 900), "CA_MW_WorkedSteel", axis="X", vertices=24)
    cylinder(parts, f"RollerHub_{y}", 110, 520, (-3140, y, 900), "CA_MW_FoundryCharcoal", axis="X", vertices=18)
for y in (-1500, 1500):
    box(parts, f"DockClamp_{y}", (760, 520, 520), (-2810, y, 1180), "CA_MW_CairnwellGreen", 42)
    cylinder(parts, f"DockClampPin_{y}", 175, 620, (-3230, y, 1180), "CA_MW_SafetyYellow", axis="X", vertices=20)
    torus(parts, f"DockCone_{y}", 330, 105, (-3290, y, 650), "CA_MW_WorkedSteel", rotation=(0, 90, 0))
box(parts, "ConnectorBlock", (620, 880, 720), (-2800, 0, 1480), "CA_MW_ServiceGrey", 40)
for y, material in ((-270, "CA_MW_StateGreen"), (0, "CA_MW_StateAmber"), (270, "CA_MW_StateBlue")):
    cylinder(parts, f"Connector_{y}", 145, 130, (-3170, y, 1510), material, axis="X", vertices=18)
box(parts, "DockPermissivePlate", (68, 1800, 330), (-3245, 0, 1920), "CA_MW_TrainAAccent", 20)
box(parts, "DockLabelPlate", (72, 1250, 160), (-3290, 0, 1690), "CA_MW_LabelWhite", 12)
assets.append(finish(
    "SM_CA_MW_PT_DieChangeDockRelease_v001", parts,
    "fixed_die_change_dock_release_visual", [3700, 5000, 2300],
    "stage local floor centre; transform-compatible with SM_CA_MW_PT_DieChangeDock_v001",
    "no_collision_presentation",
    "Roller rail, docking cones, hydraulic clamps, interlocked connector block and permissive identity plates.",
))

# Camera-side fabricated detail overlays: panel seams, access plate borders,
# fastener rows, handles and restrained hazard edges.
parts = []
for y in (-1900, 0, 1900):
    box(parts, f"VerticalSeam_{y}", (80, 75, 5200), (3200, y, 3500), "CA_MW_FoundryCharcoal", 9)
for z in (1200, 2850, 4500, 6100):
    box(parts, f"HorizontalSeam_{z}", (82, 4100, 72), (3200, 0, z), "CA_MW_FoundryCharcoal", 8)
for y in (-1780, -900, 0, 900, 1780):
    for z in (1320, 2730, 4620, 5980):
        cylinder(parts, f"PanelBolt_{y}_{z}", 68, 92, (3265, y, z), "CA_MW_WorkedSteel", axis="X", vertices=12)
for y in (-950, 950):
    box(parts, f"AccessPlate_{y}", (86, 1050, 720), (3250, y, 2050), "CA_MW_ServiceGrey", 22)
    box(parts, f"AccessHandle_{y}", (150, 85, 330), (3320, y + 360, 2050), "CA_MW_SafetyYellow", 15)
box(parts, "FrameIdentityBand", (90, 3650, 240), (3270, 0, 5400), "CA_MW_TrainAAccent", 14)
box(parts, "FrameDataPlate", (95, 1300, 170), (3300, 0, 5050), "CA_MW_LabelWhite", 10)
assets.append(finish(
    "SM_CA_MW_PT_FrameSeamFastenerPack_v001", parts,
    "fixed_camera_side_frame_release_detail", [3500, 4400, 6500],
    "stage local floor centre", "no_collision_presentation",
    "Reusable fabricated seams, fasteners, access plates, handles and restrained identity bands.",
))

# Supported utility dressing uses straight fabricated/hose segments and clamps;
# it deliberately avoids unsupported floating spaghetti.
parts = []
box(parts, "CableTray", (360, 3950, 210), (2920, 0, 4680), "CA_MW_ServiceGrey", 22)
for y in (-1650, -550, 550, 1650):
    box(parts, f"TrayBracket_{y}", (620, 140, 360), (2780, y, 4600), "CA_MW_FoundryCharcoal", 18)
routes = [
    ((3050, -1450, 4550), (3050, -1450, 2450), "CA_MW_DarkRubber"),
    ((3150, -900, 4550), (3150, -900, 3100), "CA_MW_TrainAAccent"),
    ((3050, 850, 4550), (3050, 850, 2050), "CA_MW_CairnwellGreen"),
    ((3150, 1400, 4550), (3150, 1400, 2850), "CA_MW_SafetyYellow"),
]
for index, (start, end, material) in enumerate(routes):
    pipe_between(parts, f"SupportedDrop_{index}", start, end, 105 if index != 0 else 135, material)
    y = start[1]
    for z in (2800, 3800):
        box(parts, f"RouteClamp_{index}_{z}", (180, 230, 95), (2980, y, z), "CA_MW_FoundryCharcoal", 12)
box(parts, "LowerManifold", (420, 2200, 520), (3000, 0, 1720), "CA_MW_CairnwellGreen", 38)
for y in (-800, -270, 270, 800):
    cylinder(parts, f"ManifoldCoupler_{y}", 175, 180, (3270, y, 1740), "CA_MW_WorkedSteel", axis="X", vertices=18)
assets.append(finish(
    "SM_CA_MW_PT_HoseCableDress_v001", parts,
    "fixed_supported_utility_release_detail", [3500, 4400, 5000],
    "stage local floor centre", "no_collision_presentation",
    "Supported cable tray, four distinct utility drops, clamps, manifold and couplers.",
))


def service_state_asset(name, lamp_material, role, variant):
    parts = []
    box(parts, "StateHousing", (380, 900, 1220), (3100, 1850, 2580), "CA_MW_FoundryCharcoal", 38)
    box(parts, "StateFace", (95, 690, 980), (3290, 1850, 2580), "CA_MW_ServiceGrey", 24)
    box(parts, "StateHeader", (105, 610, 175), (3350, 1850, 2920), "CA_MW_TrainAAccent", 12)
    cylinder(parts, "StateLamp", 250, 170, (3400, 1850, 2680), lamp_material, axis="X", vertices=24)
    box(parts, "StateLabelPlate", (112, 520, 150), (3360, 1850, 2380), "CA_MW_LabelWhite", 10)
    if variant == "running":
        cylinder(parts, "FlowGauge", 270, 160, (3400, 1550, 2150), "CA_MW_StateGreen", axis="X", vertices=24)
        cylinder(parts, "FlowNeedle", 38, 190, (3490, 1550, 2150), "CA_MW_LabelWhite", axis="X", vertices=12)
    elif variant == "standby":
        box(parts, "StandbyCover", (130, 520, 520), (3380, 1550, 2140), "CA_MW_StateAmber", 28)
        box(parts, "StandbyHandle", (145, 95, 300), (3480, 1750, 2140), "CA_MW_FoundryCharcoal", 12)
    else:
        box(parts, "IsolationStation", (180, 620, 640), (3400, 1550, 2130), "CA_MW_StateRed", 35)
        cylinder(parts, "IsolationHandle", 190, 230, (3540, 1550, 2200), "CA_MW_SafetyYellow", axis="X", vertices=18)
        torus(parts, "LockoutPadlock", 160, 40, (3540, 1720, 1950), "CA_MW_StateBlue", rotation=(90, 0, 0))
        box(parts, "MaintenanceTag", (110, 310, 360), (3570, 1870, 1950), "CA_MW_LabelWhite", 12)
    return finish(
        name, parts, role, [3700, 2500, 3400], "stage local floor centre",
        "no_collision_presentation",
        f"Distinct {variant} service-state module; geometry and state material are intentionally non-identical.",
    )


assets.extend([
    service_state_asset(
        "SM_CA_MW_PT_ServiceStateRunning_v001", "CA_MW_StateGreen",
        "fixed_service_state_running", "running"),
    service_state_asset(
        "SM_CA_MW_PT_ServiceStateStandby_v001", "CA_MW_StateAmber",
        "fixed_service_state_standby", "standby"),
    service_state_asset(
        "SM_CA_MW_PT_ServiceStateMaintenance_v001", "CA_MW_StateRed",
        "fixed_service_state_maintenance", "maintenance"),
])

blend_path = OUT / "CA_MW_PressTrain_ReleaseDetail_v001.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
manifest = {
    "$schema": "cairnwell/source/press-train-release-detail-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "authority": "Docs/PRESS_TRAINS_IMPLEMENTATION_AUTHORITY.md; Pro Sheets 04/05",
    "source_blend": blend_path.name,
    "coordinate_system": "+X operator/HMI/CCTV side, -X die-change side, +Y material flow, +Z up; millimetres",
    "world_placement": "TBC_NOT_INVENTED",
    "assets": assets,
    "promotion_authorized": False,
    "press_shop_complete": False,
}
(OUT / "PRESS_TRAIN_RELEASE_DETAIL_MANIFEST_v001.json").write_text(
    json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps({
    "status": "PASS__PRESS_TRAIN_RELEASE_DETAIL_V001_BUILT__SOURCE_AUDIT_AND_UNREAL_GATES_REQUIRED__NOT_PROMOTED",
    "asset_count": len(assets),
    "assets": [{"asset": row["asset"], "dimensions_mm": row["measured_dimensions_mm"]} for row in assets],
}, indent=2))
