"""Build Sheet-03-directed PR-010 v103 installed-service and identity modules."""

import bpy
import json
import math
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT = ROOT / "SourceAssets/PR010/FourLaneBuffer/ReleaseArt_v103"
FBX = OUT / "FBX"
OUT.mkdir(parents=True, exist_ok=True)
FBX.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.length_unit = "MILLIMETERS"
scene.unit_settings.scale_length = 1.0

palette = {
    "CA_MW_FoundryCharcoal": ((0.014, 0.020, 0.022, 1), 0.10, 0.62),
    "CA_MW_CairnwellGreen": ((0.020, 0.130, 0.100, 1), 0.08, 0.60),
    "CA_MW_SafetyYellow": ((0.68, 0.38, 0.005, 1), 0.05, 0.64),
    "CA_MW_ServiceGrey": ((0.25, 0.29, 0.30, 1), 0.45, 0.58),
    "CA_MW_WorkedSteel": ((0.12, 0.15, 0.16, 1), 0.80, 0.55),
    "CA_MW_IdentityFace": ((0.64, 0.68, 0.66, 1), 0.30, 0.72),
}
mats = {}
for name, (colour, metallic, roughness) in palette.items():
    material = bpy.data.materials.new(name)
    material.diffuse_color = colour
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = colour
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    mats[name] = material
assets = {}


def box(name, dims, loc, material, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=tuple(value / 1000 for value in loc))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = tuple(value / 1000 for value in dims)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mats[material])
    if bevel:
        modifier = obj.modifiers.new("EdgeBevel", "BEVEL")
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
    obj.data.materials.append(mats[material])
    return obj


def join_asset(name, parts, expected, notes):
    bpy.ops.object.select_all(action="DESELECT")
    for part in parts:
        part.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = name
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")
    assets[name] = {"object": obj, "expected_dimensions_mm": expected, "notes": notes}


# Repeated installed-service bank: separated power/control/air routes, drops, glands and boxes.
parts = [
    box("LowerSupport", (2700, 60, 70), (0, 0, 300), "CA_MW_FoundryCharcoal", bevel=5),
    box("UpperSupport", (2700, 60, 70), (0, 0, 850), "CA_MW_FoundryCharcoal", bevel=5),
]
for y, z, material in ((-200, 1040, "CA_MW_SafetyYellow"), (0, 1040, "CA_MW_CairnwellGreen"), (200, 1040, "CA_MW_ServiceGrey")):
    parts.append(cylinder(f"HorizontalRoute_{y}", 70, 2700, (0, y, z), material, axis="X"))
for index, x in enumerate((-1100, -660, -220, 220, 660, 1100)):
    material = ("CA_MW_SafetyYellow", "CA_MW_CairnwellGreen", "CA_MW_ServiceGrey")[index % 3]
    y = (-200, 0, 200)[index % 3]
    parts.append(cylinder(f"Drop_{index}", 70, 760, (x, y, 660), material))
    parts.append(box(f"Junction_{index}", (260, 170, 240), (x, y, 160), "CA_MW_FoundryCharcoal", bevel=18))
    parts.append(box(f"JunctionFace_{index}", (210, 18, 175), (x, y - 94, 160), "CA_MW_ServiceGrey", bevel=8))
    parts.append(cylinder(f"CableGland_{index}", 92, 80, (x, y, 310), "CA_MW_WorkedSteel"))
for x in (-1250, -850, -450, -50, 350, 750, 1150):
    parts.append(box(f"Clamp_{x}", (45, 500, 120), (x, 0, 1040), "CA_MW_FoundryCharcoal", bevel=4))
join_asset(
    "SM_CA_MW_PR010_InstalledServiceBank_v103", parts, [2700, 588, 1060],
    "Repeated visible power/control/air routes with vertical drops, glands and junction boxes")

# Three removable access hatches with hinge barrels, fasteners, vents and yellow handles.
parts = [
    box("HatchHeader", (2700, 70, 50), (0, 0, 625), "CA_MW_FoundryCharcoal", bevel=5),
    box("HatchSill", (2700, 70, 50), (0, 0, 25), "CA_MW_FoundryCharcoal", bevel=5),
]
for section, x in enumerate((-900, 0, 900)):
    parts.append(box(f"HatchBody_{section}", (820, 70, 650), (x, 0, 325), "CA_MW_FoundryCharcoal", bevel=12))
    parts.append(box(f"HatchFace_{section}", (750, 22, 570), (x, -46, 325), "CA_MW_CairnwellGreen", bevel=8))
    parts.append(box(f"HatchInset_{section}", (620, 12, 320), (x, -64, 350), "CA_MW_ServiceGrey", bevel=5))
    parts.append(box(f"Handle_{section}", (35, 35, 210), (x + 300, -78, 325), "CA_MW_SafetyYellow", bevel=4))
    for hinge_z in (140, 510):
        parts.append(cylinder(f"Hinge_{section}_{hinge_z}", 48, 110, (x - 360, -65, hinge_z), "CA_MW_WorkedSteel"))
    for bolt_x in (-330, 330):
        for bolt_z in (45, 605):
            parts.append(cylinder(f"Bolt_{section}_{bolt_x}_{bolt_z}", 28, 35, (x + bolt_x, -78, bolt_z), "CA_MW_WorkedSteel", axis="Y", vertices=16))
    for vent_z in (250, 300, 350, 400, 450):
        parts.append(box(f"Vent_{section}_{vent_z}", (500, 15, 18), (x - 50, -75, vent_z), "CA_MW_FoundryCharcoal", bevel=2))
join_asset(
    "SM_CA_MW_PR010_ServiceAccessHatchSection_v103", parts, [2700, 130.5, 650],
    "Three removable service hatches with hinges, captive fasteners, vents and handles")

# CCTV-readable traceability plate sized to the existing stack face without changing stack geometry.
parts = [
    box("PlateBody", (900, 40, 320), (0, 0, 160), "CA_MW_FoundryCharcoal", bevel=18),
    box("IdentityFace", (840, 20, 260), (0, -30, 160), "CA_MW_IdentityFace", bevel=10),
    box("SafetyStripe", (48, 20, 260), (-396, -44, 160), "CA_MW_SafetyYellow", bevel=4),
]
for x in (-380, 380):
    for z in (55, 265):
        parts.append(cylinder(f"PlateBolt_{x}_{z}", 34, 40, (x, -40, z), "CA_MW_WorkedSteel", axis="Y", vertices=16))
join_asset(
    "SM_CA_MW_PR010_StackIdentityPlate_v103", parts, [900, 80, 320],
    "Enlarged stack-position identity plate for fixed CCTV and control-room views")

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
        "file": str(path.relative_to(OUT)),
        "bytes": path.stat().st_size,
        "measured_dimensions_mm": [round(value * 1000, 3) for value in obj.dimensions],
        "expected_dimensions_mm": data["expected_dimensions_mm"],
        "notes": data["notes"],
        "authority": "Pro Sheet 03 hero/service direction within retained v102 fixed envelopes",
        "material_slots": [slot.material.name for slot in obj.material_slots],
    })
blend = OUT / "CA_MW_PR010_ReleaseArt_v103.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
manifest = {
    "$schema": "cairnwell/source/pr010-release-art-v103/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "station": "PR010",
    "source_blend": blend.name,
    "blender_version": bpy.app.version_string,
    "authority": "Pro Sheet 03 plus retained v102 technical contracts",
    "assets": exports,
    "promotion_authorized": False,
}
(OUT / "PR010_RELEASE_ART_MANIFEST_v103.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps({
    "status": "PASS__PR010_V103_INSTALLED_SERVICE_IDENTITY_SOURCE_BUILT__AUDIT_UNREAL_GATES_REQUIRED__NOT_PROMOTED",
    "assets": len(exports)}, indent=2))
