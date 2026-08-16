"""Build PR-010 v101 carrier, layered stack and open-fascia release-art source."""

import bpy
import json
import math
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT = ROOT / "SourceAssets/PR010/FourLaneBuffer/ReleaseArt_v101"
FBX = OUT / "FBX"
OUT.mkdir(parents=True, exist_ok=True)
FBX.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.length_unit = "MILLIMETERS"
scene.unit_settings.scale_length = 1.0

palette = {
    "CA_MW_FoundryCharcoal": (0.018, 0.025, 0.028, 1),
    "CA_MW_CairnwellGreen": (0.025, 0.19, 0.145, 1),
    "CA_MW_SafetyYellow": (0.95, 0.57, 0.0, 1),
    "CA_MW_WorkedSteel": (0.23, 0.27, 0.29, 1),
    "CA_MW_BlankSteel": (0.34, 0.38, 0.40, 1),
    "CA_MW_White": (0.75, 0.78, 0.77, 1),
}
mats = {}
for name, colour in palette.items():
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = colour
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = colour
    bsdf.inputs["Metallic"].default_value = 0.8 if "Steel" in name else 0.15
    bsdf.inputs["Roughness"].default_value = 0.32 if "BlankSteel" in name else 0.44
    mats[name] = mat

assets = {}


def box(name, dims_mm, loc_mm, material, rot_deg=(0, 0, 0), bevel_mm=0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=tuple(v/1000 for v in loc_mm), rotation=tuple(math.radians(v) for v in rot_deg))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = tuple(v/1000 for v in dims_mm)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mats[material])
    if bevel_mm:
        modifier = obj.modifiers.new("EdgeBevel", "BEVEL")
        modifier.width = bevel_mm/1000
        modifier.segments = 2
    return obj


def cylinder(name, diameter_mm, depth_mm, loc_mm, material, axis="Z", vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=diameter_mm/2000, depth=depth_mm/1000, location=tuple(v/1000 for v in loc_mm))
    obj = bpy.context.object
    obj.name = name
    if axis == "X": obj.rotation_euler[1] = math.radians(90)
    elif axis == "Y": obj.rotation_euler[0] = math.radians(90)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    obj.data.materials.append(mats[material])
    return obj


def join_asset(name, parts, expected, notes):
    bpy.ops.object.select_all(action="DESELECT")
    for part in parts: part.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = name
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")
    assets[name] = {"object": obj, "expected_dimensions_mm": expected, "notes": notes}


# 2400 x 1900 x 180 mm engineered carrier pallet, preserving the accepted envelope.
parts = [
    box("CarrierRailL", (2400, 120, 140), (0, -890, 70), "CA_MW_SafetyYellow", bevel_mm=14),
    box("CarrierRailR", (2400, 120, 140), (0, 890, 70), "CA_MW_SafetyYellow", bevel_mm=14),
]
for x in (-1080, 0, 1080):
    parts.append(box(f"CarrierCross{x}", (120, 1660, 100), (x, 0, 50), "CA_MW_FoundryCharcoal", bevel_mm=8))
for y in (-680, -510, -340, -170, 0, 170, 340, 510, 680):
    parts.append(cylinder(f"CarrierRoll{y}", 70, 2080, (0, y, 145), "CA_MW_WorkedSteel", axis="X"))
for x in (-1110, 1110):
    for y in (-860, 860):
        parts.append(box(f"CarrierCorner{x}_{y}", (180, 180, 180), (x, y, 90), "CA_MW_SafetyYellow", bevel_mm=12))
join_asset("SM_CA_MW_PR010_CarrierPallet_v101", parts, [2400, 1900, 180], "Detailed eight-position carrier pallet; fixed presentation envelope")

# 2200 x 1700 x 500 mm identified blank stack made from visible sheet layers.
parts = []
for index in range(25):
    offset = -4 if index % 3 == 0 else (4 if index % 3 == 1 else 0)
    parts.append(box(f"BlankSheet_{index:02d}", (2180, 1680, 16), (offset, 0, 8 + index*20), "CA_MW_BlankSteel", bevel_mm=2))
parts.extend([
    box("BlankBottomDatum", (2200, 1700, 4), (0, 0, 2), "CA_MW_BlankSteel"),
    box("BlankTopDatum", (2200, 1700, 4), (0, 0, 498), "CA_MW_BlankSteel"),
    box("StackStrapL", (70, 1700, 6), (-600, 0, 497), "CA_MW_FoundryCharcoal"),
    box("StackStrapR", (70, 1700, 6), (600, 0, 497), "CA_MW_FoundryCharcoal"),
    box("StackIDPlate", (520, 12, 180), (0, -844, 275), "CA_MW_White", bevel_mm=4),
])
join_asset("SM_CA_MW_PR010_BlankStack_Layered_v101", parts, [2200, 1700, 500], "Layered identified blank stack; exact accepted material envelope")

# 2900 x 80 x 750 mm open louver fascia replacing the opaque visual panel.
parts = [
    box("FasciaTop", (2900, 80, 60), (0, 0, 720), "CA_MW_CairnwellGreen", bevel_mm=8),
    box("FasciaBottom", (2900, 80, 60), (0, 0, 30), "CA_MW_CairnwellGreen", bevel_mm=8),
    box("FasciaLeft", (60, 80, 750), (-1420, 0, 375), "CA_MW_CairnwellGreen", bevel_mm=8),
    box("FasciaRight", (60, 80, 750), (1420, 0, 375), "CA_MW_CairnwellGreen", bevel_mm=8),
    box("FasciaCentre", (45, 70, 630), (0, 0, 375), "CA_MW_CairnwellGreen", bevel_mm=5),
]
for z in (125, 225, 325, 425, 525, 625):
    parts.append(box(f"FasciaLouver{z}", (2780, 35, 30), (0, -5, z), "CA_MW_WorkedSteel", rot_deg=(18, 0, 0), bevel_mm=3))
join_asset("SM_CA_MW_PR010_FasciaLouvered_v101", parts, [2900, 80, 750], "Open service fascia within the exact accepted panel envelope")

exports = []
for name, data in assets.items():
    obj = data["object"]
    path = FBX / f"{name}.fbx"
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL", axis_forward="-Y", axis_up="Z", use_mesh_modifiers=True, add_leaf_bones=False)
    dims = [round(value*1000, 3) for value in obj.dimensions]
    exports.append({"asset": name, "file": str(path.relative_to(OUT)), "bytes": path.stat().st_size,
                    "measured_dimensions_mm": dims, "expected_dimensions_mm": data["expected_dimensions_mm"],
                    "notes": data["notes"], "material_slots": [slot.material.name for slot in obj.material_slots]})

blend = OUT / "CA_MW_PR010_ReleaseArt_v101.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
manifest = {
    "$schema": "cairnwell/source/pr010-release-art-v101/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(), "station": "PR010",
    "source_blend": blend.name, "blender_version": bpy.app.version_string,
    "authority": "Pro Sheet 03 plus retained v100 technical contracts",
    "assets": exports, "promotion_authorized": False,
}
(OUT / "PR010_RELEASE_ART_MANIFEST_v101.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps({"status": "PASS__PR010_V101_SOURCE_BUILT__AUDIT_AND_UNREAL_GATES_REQUIRED__NOT_PROMOTED", "assets": len(exports)}, indent=2))
