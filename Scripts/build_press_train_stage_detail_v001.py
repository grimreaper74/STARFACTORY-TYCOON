"""Build reusable exterior/service and endpoint detail for CCTV-first press trains."""

import bpy
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT = ROOT / "SourceAssets/PressTrains/Shared/StageDetail_v001"
FBX = OUT / "FBX"
OUT.mkdir(parents=True, exist_ok=True)
FBX.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.length_unit = "MILLIMETERS"
scene.unit_settings.scale_length = 1.0

palette = {
    "CA_MW_FoundryCharcoal": ((0.016, 0.021, 0.023, 1), 0.35, 0.58),
    "CA_MW_CairnwellGreen": ((0.018, 0.120, 0.090, 1), 0.22, 0.54),
    "CA_MW_SafetyYellow": ((0.78, 0.43, 0.008, 1), 0.18, 0.53),
    "CA_MW_WorkedSteel": ((0.12, 0.15, 0.16, 1), 0.85, 0.46),
    "CA_MW_ServiceGrey": ((0.10, 0.13, 0.14, 1), 0.42, 0.60),
    "CA_MW_TrainAAccent": ((0.035, 0.190, 0.420, 1), 0.20, 0.52),
    "CA_MW_HMIScreen": ((0.004, 0.055, 0.042, 1), 0.05, 0.25),
    "CA_MW_StateGreen": ((0.02, 0.65, 0.20, 1), 0.05, 0.30),
    "CA_MW_EStopRed": ((0.75, 0.015, 0.01, 1), 0.08, 0.38),
}
materials = {}
for name, (colour, metallic, roughness) in palette.items():
    material = bpy.data.materials.new(name)
    material.diffuse_color = colour
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = colour
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    materials[name] = material


def box(parts, name, dims, loc, material, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=tuple(v / 1000 for v in loc))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = tuple(v / 1000 for v in dims)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(materials[material])
    if bevel:
        mod = obj.modifiers.new("InstalledEdge", "BEVEL")
        mod.width = bevel / 1000
        mod.segments = 2
    parts.append(obj)
    return obj


def cylinder(parts, name, diameter, depth, loc, material, axis="Z", vertices=24):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=diameter / 2000, depth=depth / 1000,
        location=tuple(v / 1000 for v in loc),
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


def finish_asset(name, parts, envelope, role, notes):
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
    fbx_path = FBX / f"{name}.fbx"
    bpy.ops.export_scene.fbx(
        filepath=str(fbx_path), use_selection=True, apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL", axis_forward="-Y", axis_up="Z",
        use_mesh_modifiers=True, add_leaf_bones=False,
    )
    row = {
        "asset": name,
        "file": str(fbx_path.relative_to(OUT)).replace("\\", "/"),
        "bytes": fbx_path.stat().st_size,
        "sha256": hashlib.sha256(fbx_path.read_bytes()).hexdigest().upper(),
        "measured_dimensions_mm": [round(v * 1000, 3) for v in obj.dimensions],
        "planning_envelope_mm": envelope,
        "role": role,
        "pivot": "stage local floor centre",
        "collision_role": "no_collision_presentation",
        "material_slots": [slot.material.name for slot in obj.material_slots],
        "notes": notes,
    }
    bpy.data.objects.remove(obj, do_unlink=True)
    return row


assets = []

# One camera-side service pack per stage: remotely readable controls and believable utilities.
parts = []
box(parts, "ServicePedestal", (650, 700, 1750), (2600, 0, 875), "CA_MW_FoundryCharcoal", 45)
box(parts, "HMIHousing", (760, 260, 560), (2600, -350, 1840), "CA_MW_ServiceGrey", 35)
box(parts, "HMIScreen", (560, 35, 350), (2600, -498, 1870), "CA_MW_HMIScreen", 12)
box(parts, "StageIDPlate", (610, 28, 150), (2600, -515, 2220), "CA_MW_TrainAAccent", 10)
box(parts, "IsolationBox", (430, 260, 520), (2600, 360, 1280), "CA_MW_CairnwellGreen", 28)
cylinder(parts, "EStop", 125, 95, (2600, -500, 1560), "CA_MW_EStopRed", axis="Y", vertices=28)
cylinder(parts, "StateBeacon", 105, 420, (2600, 0, 2500), "CA_MW_StateGreen", vertices=24)
box(parts, "UtilityManifold", (700, 340, 390), (2600, 410, 500), "CA_MW_ServiceGrey", 28)
for xoff in (-210, 0, 210):
    cylinder(parts, f"ManifoldPort_{xoff}", 90, 190, (2600 + xoff, 650, 500), "CA_MW_SafetyYellow", axis="Y", vertices=18)
for z in (420, 690, 960):
    cylinder(parts, f"ServiceConduit_{z}", 70, 1350, (2280, 0, z), "CA_MW_WorkedSteel", axis="Y", vertices=14)
assets.append(finish_asset(
    "SM_CA_MW_PT_StageServicePack_v001", parts, [6500, 5000, 6500],
    "fixed_stage_service_and_remote_hmi",
    "Reusable camera-side HMI, E-stop, isolation, stage ID, beacon, manifold and supported conduits.",
))

# S01: blank-stack preparation and destack presentation, with no exposed worker operation.
parts = []
box(parts, "BlankStackBed", (4300, 3200, 360), (0, 0, 420), "CA_MW_WorkedSteel", 45)
for x in (-2050, 2050):
    box(parts, f"StackStop_{x}", (220, 3300, 760), (x, 0, 820), "CA_MW_SafetyYellow", 22)
for y in (-1400, 1400):
    box(parts, f"GuideRail_{y}", (4500, 180, 260), (0, y, 760), "CA_MW_ServiceGrey", 20)
box(parts, "BlankStack", (3600, 2500, 620), (0, 0, 910), "CA_MW_WorkedSteel", 22)
box(parts, "DestackBridge", (5100, 580, 520), (0, 0, 3900), "CA_MW_CairnwellGreen", 55)
for x in (-2200, 2200):
    box(parts, f"BridgePost_{x}", (420, 650, 3500), (x, 0, 2200), "CA_MW_FoundryCharcoal", 48)
cylinder(parts, "LiftColumn", 440, 2100, (0, 0, 2750), "CA_MW_ServiceGrey", vertices=28)
box(parts, "VacuumHead", (3100, 2050, 260), (0, 0, 1950), "CA_MW_ServiceGrey", 30)
for x in (-1200, -400, 400, 1200):
    for y in (-760, 760):
        cylinder(parts, f"VacuumCup_{x}_{y}", 210, 250, (x, y, 1710), "CA_MW_FoundryCharcoal", vertices=20)
for y in (-1100, 1100):
    box(parts, f"MagneticFanner_{y}", (340, 280, 1050), (1700, y, 1320), "CA_MW_SafetyYellow", 30)
assets.append(finish_asset(
    "SM_CA_MW_PT_S01DestackDetail_v001", parts, [6500, 5000, 6500],
    "fixed_s01_destack_and_blank_stack_presentation",
    "Enclosed-line blank-stack bed, stops, fanners and vacuum destack head; presentation only.",
))

# S07: outfeed conveying and inspection arch, readable externally from management cameras.
parts = []
box(parts, "OutfeedFrame", (5000, 3000, 480), (0, 0, 520), "CA_MW_FoundryCharcoal", 48)
for x in range(-2100, 2101, 600):
    cylinder(parts, f"OutfeedRoller_{x}", 180, 2700, (x, 0, 850), "CA_MW_WorkedSteel", axis="Y", vertices=20)
for x in (-2100, 2100):
    box(parts, f"InspectPost_{x}", (360, 420, 3100), (x, 0, 2350), "CA_MW_CairnwellGreen", 42)
box(parts, "InspectArch", (4700, 520, 520), (0, 0, 3880), "CA_MW_CairnwellGreen", 45)
for x in (-1450, 0, 1450):
    box(parts, f"InspectionLight_{x}", (850, 180, 120), (x, -350, 3520), "CA_MW_StateGreen", 14)
box(parts, "VisionCabinet", (850, 760, 1850), (2450, 700, 1200), "CA_MW_ServiceGrey", 45)
box(parts, "VisionScreen", (610, 28, 390), (2450, 305, 1680), "CA_MW_HMIScreen", 12)
box(parts, "AcceptedPanelStillage", (3600, 2600, 380), (0, 0, 1180), "CA_MW_WorkedSteel", 30)
assets.append(finish_asset(
    "SM_CA_MW_PT_S07UnloadInspectDetail_v001", parts, [6500, 5000, 6500],
    "fixed_s07_outfeed_and_inspection_presentation",
    "Roller outfeed, vision/light arch, remote cabinet and panel stillage; presentation only.",
))

# Mid-train process service cues prevent five identical press cabinets.
parts = []
box(parts, "ScrapChute", (1050, 1250, 1550), (2350, 0, 920), "CA_MW_ServiceGrey", 38)
box(parts, "ScrapBin", (1500, 1650, 900), (2350, 0, 450), "CA_MW_FoundryCharcoal", 28)
box(parts, "LubeReservoir", (900, 760, 1320), (2350, 1200, 760), "CA_MW_CairnwellGreen", 42)
cylinder(parts, "LubePump", 520, 720, (2350, 1200, 1680), "CA_MW_ServiceGrey", vertices=28)
for y in (-520, 0, 520):
    cylinder(parts, f"ProcessRoute_{y}", 85, 1500, (2000, y, 2050), "CA_MW_SafetyYellow", axis="Y", vertices=14)
assets.append(finish_asset(
    "SM_CA_MW_PT_MidTrainProcessService_v001", parts, [6500, 5000, 6500],
    "fixed_mid_train_scrap_lube_service_presentation",
    "Reusable scrap chute/bin, lubrication reservoir/pump and process routes for stage differentiation.",
))

blend_path = OUT / "CA_MW_PressTrain_StageDetail_v001.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
manifest = {
    "$schema": "cairnwell/source/press-train-stage-detail-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "authority": "Docs/PRESS_TRAINS_IMPLEMENTATION_AUTHORITY.md; Pro Sheets 04/05",
    "source_blend": blend_path.name,
    "coordinate_system": "+X across train, +Y material flow, +Z up; millimetres",
    "world_placement": "TBC_NOT_INVENTED",
    "design_model": "CCTV-first enclosed press line; hidden mechanism is not simulated",
    "assets": assets,
    "promotion_authorized": False,
    "press_shop_complete": False,
}
(OUT / "PRESS_TRAIN_STAGE_DETAIL_MANIFEST_v001.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps({
    "status": "PASS__PRESS_TRAIN_STAGE_DETAIL_V001_BUILT__SOURCE_AUDIT_AND_UNREAL_GATES_REQUIRED__NOT_PROMOTED",
    "assets": [{"asset": row["asset"], "dimensions_mm": row["measured_dimensions_mm"]} for row in assets],
}, indent=2))
