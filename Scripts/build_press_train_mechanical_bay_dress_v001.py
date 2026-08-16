"""Build a dimensioned reusable visible-mechanics dress module for press stages."""

import bpy
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT = ROOT / "SourceAssets/PressTrains/Shared/MechanicalBay_v001"
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


def box(name, dims, loc, material, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=tuple(value / 1000 for value in loc))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = tuple(value / 1000 for value in dims)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(materials[material])
    if bevel:
        mod = obj.modifiers.new("MachinedEdge", "BEVEL")
        mod.width = bevel / 1000
        mod.segments = 2
    return obj


def cylinder(name, diameter, depth, loc, material, axis="Z", vertices=24):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=diameter / 2000,
        depth=depth / 1000,
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
    return obj


parts = [
    box("LowerPlaten", (5400, 3900, 520), (0, 0, 780), "CA_MW_WorkedSteel", 45),
    box("BolsterGuideLeft", (360, 4100, 260), (-2050, 0, 1160), "CA_MW_ServiceGrey", 25),
    box("BolsterGuideRight", (360, 4100, 260), (2050, 0, 1160), "CA_MW_ServiceGrey", 25),
    box("Crosshead", (5000, 3300, 850), (0, 0, 5350), "CA_MW_FoundryCharcoal", 65),
    box("RamBlock", (3600, 2600, 700), (0, 0, 4350), "CA_MW_CairnwellGreen", 55),
    box("SlideFace", (3900, 2800, 260), (0, 0, 3920), "CA_MW_WorkedSteel", 30),
    box("CameraSideGearbox", (850, 1450, 1250), (2650, 1050, 2650), "CA_MW_CairnwellGreen", 70),
    box("GearboxAccent", (100, 1150, 180), (3080, 1050, 2870), "CA_MW_TrainAAccent", 18),
]

# Four heavy tie rods and collars give the open bay a believable press-frame read.
for x in (-1850, 1850):
    for y in (-1250, 1250):
        parts.append(cylinder(f"TieRod_{x}_{y}", 360, 3900, (x, y, 3200), "CA_MW_WorkedSteel", vertices=28))
        parts.append(cylinder(f"TieRodCollarLow_{x}_{y}", 540, 190, (x, y, 1430), "CA_MW_SafetyYellow", vertices=28))
        parts.append(cylinder(f"TieRodCollarHigh_{x}_{y}", 540, 190, (x, y, 4930), "CA_MW_SafetyYellow", vertices=28))

# Twin visible ram cylinders, a camera-facing drive pod and supported service routes.
for y in (-820, 820):
    parts.append(cylinder(f"RamCylinder_{y}", 520, 1850, (0, y, 4550), "CA_MW_ServiceGrey", vertices=28))
    parts.append(cylinder(f"RamRod_{y}", 230, 1500, (0, y, 3300), "CA_MW_WorkedSteel", vertices=24))
parts.extend([
    cylinder("DriveMotor", 1050, 720, (2800, 1050, 2650), "CA_MW_ServiceGrey", axis="X", vertices=32),
    cylinder("UpperHydraulicRoute", 130, 4200, (2500, 0, 4700), "CA_MW_SafetyYellow", axis="Y", vertices=16),
    cylinder("LowerLubeRoute", 95, 4200, (2450, 0, 1850), "CA_MW_CairnwellGreen", axis="Y", vertices=16),
])
for y in (-1700, -600, 600, 1700):
    parts.append(box(f"UtilitySupport_{y}", (220, 180, 620), (2500, y, 4200), "CA_MW_FoundryCharcoal", 18))

bpy.ops.object.select_all(action="DESELECT")
for part in parts:
    part.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
obj = bpy.context.object
obj.name = "SM_CA_MW_PT_MechanicalBayDress_v001"
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
scene.cursor.location = (0, 0, 0)
bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")

fbx_path = FBX / f"{obj.name}.fbx"
bpy.ops.object.select_all(action="DESELECT")
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.ops.export_scene.fbx(
    filepath=str(fbx_path), use_selection=True, apply_unit_scale=True,
    apply_scale_options="FBX_SCALE_ALL", axis_forward="-Y", axis_up="Z",
    use_mesh_modifiers=True, add_leaf_bones=False,
)
blend_path = OUT / "CA_MW_PressTrain_MechanicalBay_v001.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
manifest = {
    "$schema": "cairnwell/source/press-train-mechanical-bay-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "authority": "Docs/PRESS_TRAINS_IMPLEMENTATION_AUTHORITY.md; Pro Sheets 04/05",
    "source_blend": blend_path.name,
    "coordinate_system": "+X across train, +Y material flow, +Z up; millimetres",
    "world_placement": "TBC_NOT_INVENTED",
    "assets": [{
        "asset": obj.name,
        "file": str(fbx_path.relative_to(OUT)).replace("\\", "/"),
        "bytes": fbx_path.stat().st_size,
        "sha256": hashlib.sha256(fbx_path.read_bytes()).hexdigest().upper(),
        "measured_dimensions_mm": [round(value * 1000, 3) for value in obj.dimensions],
        "planning_envelope_mm": [6500, 5000, 6500],
        "role": "fixed_visible_mechanical_bay_dress",
        "pivot": "stage local floor centre",
        "collision_role": "no_collision_presentation",
        "material_slots": [slot.material.name for slot in obj.material_slots],
        "notes": "Reusable visible tie rods, platen, slide, cylinders, drive and supported utilities; not a full physical press simulation"
    }],
    "promotion_authorized": False,
    "press_shop_complete": False,
}
(OUT / "PRESS_TRAIN_MECHANICAL_BAY_MANIFEST_v001.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps({"status": "PASS__PRESS_TRAIN_MECHANICAL_BAY_V001_BUILT__SOURCE_AUDIT_AND_UNREAL_GATES_REQUIRED__NOT_PROMOTED", "dimensions_mm": manifest["assets"][0]["measured_dimensions_mm"]}, indent=2))
