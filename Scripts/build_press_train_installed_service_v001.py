"""Build reusable installed-service and stage-variant detail for press trains."""

import bpy
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT = ROOT / "SourceAssets/PressTrains/Shared/InstalledService_v001"
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
    "CA_MW_TaskWhite": ((0.72, 0.80, 0.77, 1), 0.05, 0.30),
    "CA_MW_OilAmber": ((0.42, 0.12, 0.003, 1), 0.10, 0.42),
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


def cylinder(parts, name, diameter, depth, loc, material, axis="Z", vertices=20):
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


def finish(name, parts, role, notes):
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
        "asset": name, "file": str(path.relative_to(OUT)).replace("\\", "/"),
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper(),
        "measured_dimensions_mm": [round(v * 1000, 3) for v in obj.dimensions],
        "planning_envelope_mm": [6500, 5000, 6500], "role": role,
        "pivot": "stage local floor centre", "collision_role": "no_collision_presentation",
        "material_slots": [slot.material.name for slot in obj.material_slots], "notes": notes,
    }
    bpy.data.objects.remove(obj, do_unlink=True)
    return row


assets = []

# Camera-side installed bank: access panels, pipework, manifolds and fastener rows.
parts = []
box(parts, "ServiceBackplate", (260, 1850, 2850), (2920, 650, 2700), "CA_MW_FoundryCharcoal", 30)
for index, z in enumerate((1820, 2520, 3220), start=1):
    box(parts, f"AccessHatch_{index}", (55, 1450, 540), (3078, 650, z), "CA_MW_ServiceGrey", 25)
    for y in (50, 1250):
        cylinder(parts, f"HatchFastener_{index}_{y}", 55, 70, (3125, y, z), "CA_MW_WorkedSteel", axis="X", vertices=16)
for offset, material in ((-560, "CA_MW_SafetyYellow"), (-220, "CA_MW_CairnwellGreen"), (140, "CA_MW_WorkedSteel"), (500, "CA_MW_TrainAAccent")):
    cylinder(parts, f"VerticalRoute_{offset}", 95, 2500, (3140, 650 + offset, 2720), material, vertices=16)
    box(parts, f"RouteClampLow_{offset}", (120, 180, 90), (3090, 650 + offset, 1850), "CA_MW_FoundryCharcoal", 12)
    box(parts, f"RouteClampHigh_{offset}", (120, 180, 90), (3090, 650 + offset, 3500), "CA_MW_FoundryCharcoal", 12)
box(parts, "ServiceManifold", (300, 1550, 360), (3080, 650, 4180), "CA_MW_CairnwellGreen", 32)
for y in (-500, 0, 500):
    cylinder(parts, f"ManifoldValve_{y}", 150, 115, (3270, 650 + y, 4180), "CA_MW_SafetyYellow", axis="X", vertices=20)
assets.append(finish(
    "SM_CA_MW_PT_InstalledServiceBank_v001", parts,
    "fixed_camera_side_installed_service_bank",
    "Reusable access hatches, fasteners, supported colour-coded utilities, manifold and valves.",
))

# Die-change side interface remains opposite the HMI side as required by Sheet 04.
parts = []
box(parts, "DockBeam", (520, 4300, 520), (-2880, 0, 620), "CA_MW_FoundryCharcoal", 45)
for y in (-1650, -550, 550, 1650):
    cylinder(parts, f"DockRoller_{y}", 240, 420, (-3140, y, 850), "CA_MW_WorkedSteel", axis="X", vertices=24)
    box(parts, f"ClampBody_{y}", (560, 360, 420), (-2850, y, 1180), "CA_MW_CairnwellGreen", 35)
    cylinder(parts, f"ClampPin_{y}", 150, 520, (-3180, y, 1180), "CA_MW_SafetyYellow", axis="X", vertices=20)
box(parts, "PermissivePlate", (55, 1500, 320), (-3205, 0, 1560), "CA_MW_TrainAAccent", 20)
assets.append(finish(
    "SM_CA_MW_PT_DieChangeDock_v001", parts,
    "fixed_die_change_dock_and_clamp_interface",
    "Opposite-side die cart rollers, clamp bodies, pins and permissive plate; presentation only.",
))

# S04 trim-specific scrap extraction is deliberately different from generic service hardware.
parts = []
box(parts, "TrimChuteUpper", (1250, 1450, 1350), (2200, 0, 1800), "CA_MW_ServiceGrey", 42)
box(parts, "TrimChuteLower", (1600, 1800, 850), (2200, 0, 760), "CA_MW_FoundryCharcoal", 35)
box(parts, "ScrapWindow", (80, 1050, 420), (2840, 0, 1750), "CA_MW_OilAmber", 18)
for y in (-650, 650):
    cylinder(parts, f"ExtractionRoute_{y}", 160, 2150, (2850, y, 2900), "CA_MW_SafetyYellow", vertices=18)
box(parts, "TrimServiceID", (55, 1200, 220), (3000, 0, 3450), "CA_MW_TrainAAccent", 16)
assets.append(finish(
    "SM_CA_MW_PT_S04TrimScrapService_v001", parts,
    "fixed_s04_trim_scrap_extraction",
    "Trim chute, monitored scrap window, extraction routes and Train A stage accent.",
))

# S05 pierce-specific slug collection has small dense receivers and monitored bins.
parts = []
for y in (-1050, -350, 350, 1050):
    cylinder(parts, f"SlugDrop_{y}", 180, 1450, (2300, y, 1750), "CA_MW_WorkedSteel", vertices=18)
    box(parts, f"SlugReceiver_{y}", (760, 520, 620), (2300, y, 720), "CA_MW_FoundryCharcoal", 28)
    box(parts, f"ReceiverWindow_{y}", (55, 310, 210), (2710, y, 760), "CA_MW_OilAmber", 12)
box(parts, "PierceHeader", (720, 2850, 420), (2300, 0, 2700), "CA_MW_CairnwellGreen", 35)
box(parts, "PierceServiceID", (55, 1300, 220), (2690, 0, 3000), "CA_MW_TrainAAccent", 16)
assets.append(finish(
    "SM_CA_MW_PT_S05PierceSlugService_v001", parts,
    "fixed_s05_pierce_slug_collection",
    "Four slug drops and receivers, monitored windows, common header and stage identity.",
))

# Visible task fixture is paired with a restrained Unreal light, not used as broad exposure fill.
parts = []
box(parts, "FixtureHousing", (240, 1600, 220), (2920, 0, 4200), "CA_MW_FoundryCharcoal", 28)
box(parts, "FixtureLens", (55, 1320, 105), (3068, 0, 4150), "CA_MW_TaskWhite", 14)
for y in (-720, 720):
    box(parts, f"FixtureBracket_{y}", (320, 110, 420), (2780, y, 4300), "CA_MW_ServiceGrey", 18)
assets.append(finish(
    "SM_CA_MW_PT_LocalTaskFixture_v001", parts,
    "fixed_camera_side_local_task_fixture",
    "Installed service-bay luminaire housing, lens and brackets; paired with local Unreal light.",
))

blend_path = OUT / "CA_MW_PressTrain_InstalledService_v001.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
manifest = {
    "$schema": "cairnwell/source/press-train-installed-service-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "authority": "Docs/PRESS_TRAINS_IMPLEMENTATION_AUTHORITY.md; Pro Sheets 04/05",
    "source_blend": blend_path.name,
    "coordinate_system": "+X operator/HMI/CCTV side, -X die-change side, +Y material flow, +Z up; millimetres",
    "world_placement": "TBC_NOT_INVENTED",
    "assets": assets, "promotion_authorized": False, "press_shop_complete": False,
}
(OUT / "PRESS_TRAIN_INSTALLED_SERVICE_MANIFEST_v001.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps({
    "status": "PASS__PRESS_TRAIN_INSTALLED_SERVICE_V001_BUILT__SOURCE_AUDIT_AND_UNREAL_GATES_REQUIRED__NOT_PROMOTED",
    "assets": [{"asset": row["asset"], "dimensions_mm": row["measured_dimensions_mm"]} for row in assets],
}, indent=2))
