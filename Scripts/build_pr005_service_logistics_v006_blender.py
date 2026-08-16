"""Author a detailed, contained PR005 service-logistics dressing kit.

This is presentation geometry only. It replaces the six v053 vendor blockout
actors in an isolated successor and never becomes production-flow authority.
"""

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "SourceAssets/Candidate/PressShop/PR005/ServiceLogistics_v006"
DERIVED = ROOT / "SourceAssets/Candidate/PressShop/PR005/ServiceLogistics_UnrealDerived_v007"
ASSET = "SM_CA_MW_PR005_ServiceLogistics_Static_v006"
DERIVED_ASSET = "SM_CA_MW_PR005_ServiceLogistics_Static_v007"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def mat(name, colour, metallic, roughness):
    value = bpy.data.materials.new(name)
    value.diffuse_color = (*colour, 1.0)
    value.metallic = metallic
    value.roughness = roughness
    return value


def box(name, dimensions, location, material, bevel=0.008):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    if bevel:
        modifier = obj.modifiers.new("FabricatedEdge", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    return obj


def cylinder(name, radius, depth, location, rotation, material, vertices=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    bevel = obj.modifiers.new("EdgeBreak", "BEVEL")
    bevel.width = 0.006
    bevel.segments = 2
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    return obj


def raised_text(name, body, location, size, material):
    bpy.ops.object.text_add(location=location, rotation=(math.radians(90.0), 0.0, 0.0))
    obj = bpy.context.object
    obj.name = name
    obj.data.body = body
    obj.data.align_x = "CENTER"
    obj.data.align_y = "CENTER"
    obj.data.size = size
    obj.data.extrude = 0.006
    obj.data.bevel_depth = 0.002
    obj.data.materials.append(material)
    bpy.ops.object.convert(target="MESH")
    return obj


def export(obj, path):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(
        filepath=str(path), use_selection=True, object_types={"MESH"},
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
        add_leaf_bones=False, bake_anim=False, mesh_smooth_type="FACE")


def bounds_mm(obj):
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    low = Vector((min(v.x for v in corners), min(v.y for v in corners), min(v.z for v in corners)))
    high = Vector((max(v.x for v in corners), max(v.y for v in corners), max(v.z for v in corners)))
    return ([round(v * 1000.0, 3) for v in low],
            [round(v * 1000.0, 3) for v in high],
            [round(v * 1000.0, 3) for v in high - low])


if SOURCE.exists() or DERIVED.exists():
    raise RuntimeError("refusing to overwrite preserved PR005 service-logistics source")
(SOURCE / "Exports").mkdir(parents=True)
(DERIVED / "Exports").mkdir(parents=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.length_unit = "METERS"
scene.unit_settings.scale_length = 1.0

charcoal = mat("CA_MW_LogisticsCharcoal", (0.025, 0.032, 0.034), 0.62, 0.46)
blue = mat("CA_MW_ReturnBlue", (0.018, 0.075, 0.145), 0.42, 0.48)
yellow = mat("CA_MW_SafetyYellow", (0.67, 0.32, 0.008), 0.25, 0.42)
orange = mat("CA_MW_ServiceOrange", (0.45, 0.15, 0.015), 0.12, 0.54)
steel = mat("CA_MW_HardwareSteel", (0.28, 0.31, 0.32), 0.88, 0.26)
white = mat("CA_MW_LabelWhite", (0.73, 0.75, 0.72), 0.02, 0.70)
rubber = mat("CA_MW_RubberBlack", (0.006, 0.007, 0.007), 0.02, 0.86)
parts = []

# Return stillage, left bay: open framed construction, visible casters and trays.
sx, sy = -1.02, 0.0
for y in (-0.48, 0.48):
    parts.append(box("StillageBaseRail", (1.42, 0.09, 0.12), (sx, y, 0.16), blue))
for x in (sx - 0.66, sx + 0.66):
    parts.append(box("StillageBaseCross", (0.09, 1.05, 0.12), (x, sy, 0.16), blue))
    for y in (-0.48, 0.48):
        parts.append(box("StillagePost", (0.075, 0.075, 1.34), (x, y, 0.80), blue, 0.006))
for z in (0.56, 1.08, 1.45):
    for y in (-0.48, 0.48):
        parts.append(box("StillageSideRail", (1.42, 0.055, 0.065), (sx, y, z), blue, 0.005))
for x in (sx - 0.66, sx + 0.66):
    for z in (0.56, 1.08, 1.45):
        parts.append(box("StillageEndRail", (0.055, 1.02, 0.065), (x, sy, z), blue, 0.005))
for x in (sx - 0.52, sx + 0.52):
    for y in (-0.40, 0.40):
        parts.append(cylinder("StillageCaster", 0.095, 0.07, (x, y, 0.07), (math.radians(90.0), 0.0, 0.0), rubber))
        parts.append(box("CasterYoke", (0.09, 0.07, 0.14), (x, y, 0.14), steel, 0.004))
for index, z in enumerate((0.38, 0.73, 1.08), 1):
    parts.append(box(f"ReturnTray_{index}", (1.18, 0.82, 0.07), (sx, sy, z), charcoal, 0.01))
    for x in (sx - 0.48, sx + 0.48):
        parts.append(box("TrayDivider", (0.035, 0.72, 0.18), (x, sy, z + 0.10), charcoal, 0.004))
parts.append(box("ReturnLabelPlate", (0.72, 0.03, 0.25), (sx, -0.525, 1.26), blue, 0.008))
parts.append(raised_text("ReturnLabel", "PR-005 RETURN", (sx, -0.548, 1.27), 0.105, white))

# Service pallet and three lidded, handled crates.
px, py = 0.65, 0.04
for y in (-0.42, 0.0, 0.42):
    parts.append(box("PalletSlat", (1.28, 0.18, 0.075), (px, py + y, 0.13), blue, 0.006))
for x in (px - 0.48, px, px + 0.48):
    parts.append(box("PalletRunner", (0.16, 1.04, 0.09), (x, py, 0.06), blue, 0.005))
crate_specs = ((0.28, -0.24, 0.55, "SERVICE"), (0.95, -0.24, 0.48, "SPARES"), (0.63, 0.30, 0.62, "BANDING"))
for index, (x, y, width, label) in enumerate(crate_specs, 1):
    parts.append(box(f"CrateBody_{index}", (width, 0.48, 0.35), (x, y, 0.37), orange, 0.025))
    parts.append(box(f"CrateLid_{index}", (width + 0.035, 0.515, 0.055), (x, y, 0.57), charcoal, 0.012))
    for side in (-1.0, 1.0):
        parts.append(box("CrateHandle", (0.12, 0.025, 0.045), (x + side * (width / 2.0 + 0.018), y, 0.43), steel, 0.004))
    parts.append(box("CrateLabelPlate", (min(width - 0.10, 0.42), 0.012, 0.11), (x, y - 0.248, 0.40), white, 0.002))
    parts.append(raised_text(f"CrateLabel_{index}", label, (x, y - 0.257, 0.40), 0.055, charcoal))

# Narrow maintenance consumables trolley, kept inside the inherited logistics bay.
tx, ty = 1.62, 0.02
for z in (0.25, 0.67):
    parts.append(box("TrolleyShelf", (0.62, 0.82, 0.065), (tx, ty, z), charcoal, 0.012))
for x in (tx - 0.27, tx + 0.27):
    for y in (ty - 0.36, ty + 0.36):
        parts.append(box("TrolleyPost", (0.055, 0.055, 1.02), (x, y, 0.58), yellow, 0.005))
        parts.append(cylinder("TrolleyWheel", 0.075, 0.045, (x, y, 0.08), (math.radians(90.0), 0.0, 0.0), rubber))
parts.append(box("TrolleyHandleTop", (0.62, 0.055, 0.055), (tx, ty + 0.36, 1.13), steel, 0.006))
parts.append(box("TrolleyLabelPlate", (0.42, 0.025, 0.20), (tx, ty - 0.422, 0.88), blue, 0.006))
parts.append(raised_text("TrolleyLabel", "SERVICE", (tx, ty - 0.441, 0.89), 0.075, white))
for x in (tx - 0.17, tx + 0.12):
    parts.append(cylinder("ServiceCan", 0.10, 0.28, (x, ty, 0.48), (0.0, 0.0, 0.0), steel))
    parts.append(box("ServiceCanCap", (0.06, 0.06, 0.05), (x, ty, 0.65), yellow, 0.004))

bpy.ops.object.select_all(action="DESELECT")
for part in parts:
    part.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
asset = bpy.context.object
asset.name = ASSET
asset.data.name = ASSET
bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
asset["authority"] = "STATIC_PRESENTATION_ONLY_NO_PRODUCTION_FLOW_AUTHORITY"
asset["replacement_scope"] = "SIX_RETAINED_V053_LOGISTICS_BLOCKOUT_ACTORS_ONLY"
asset["route_clearance"] = "EXACT_WORLD_PLACEMENT_AND_NAVIGATION_GATE_REQUIRED"
low, high, dimensions = bounds_mm(asset)
blend = SOURCE / "PR005_ServiceLogistics_Candidate_v006.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
source_fbx = SOURCE / "Exports" / f"{ASSET}.fbx"
export(asset, source_fbx)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(source_fbx), use_anim=False)
meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
if len(meshes) != 1:
    raise RuntimeError(f"expected one joined mesh, got {len(meshes)}")
derived = meshes[0]
derived.data.transform(Matrix.Scale(100.0, 4))
derived.name = DERIVED_ASSET
derived.data.name = DERIVED_ASSET
derived_fbx = DERIVED / "Exports" / f"{DERIVED_ASSET}.fbx"
export(derived, derived_fbx)

generated = datetime.now(timezone.utc).isoformat()
common = {
    "generated_utc": generated,
    "expected_bounds_min_mm": low,
    "expected_bounds_max_mm": high,
    "expected_dimensions_mm": dimensions,
    "pivot_m": [0.0, 0.0, 0.0],
    "material_slots": [
        "CA_MW_LogisticsCharcoal", "CA_MW_ReturnBlue", "CA_MW_SafetyYellow",
        "CA_MW_ServiceOrange", "CA_MW_HardwareSteel", "CA_MW_LabelWhite", "CA_MW_RubberBlack"],
    "runtime_authority": "UNCHANGED_PR005_STATION_AND_MATERIAL_FLOW",
    "promotion_authorized": False,
}
source_manifest = dict(common, **{
    "$schema": "cairnwell/source/pr005-service-logistics-v006/v1",
    "status": "SOURCE_AUTHORED__UNREAL_INTAKE_AND_ROUTE_GATES_REQUIRED__NOT_PROMOTED",
    "asset_name": ASSET, "fbx": f"Exports/{ASSET}.fbx", "blend": blend.name,
    "sha256": sha256(source_fbx), "blend_sha256": sha256(blend),
})
derived_manifest = dict(common, **{
    "$schema": "cairnwell/source/pr005-service-logistics-unreal-derived-v007/v1",
    "status": "DERIVED_SCALE_COMPENSATION_ONLY__UNREAL_INTAKE_REQUIRED__NOT_PROMOTED",
    "asset_name": DERIVED_ASSET, "fbx": f"Exports/{DERIVED_ASSET}.fbx",
    "sha256": sha256(derived_fbx), "source_fbx_sha256": sha256(source_fbx),
    "local_vertex_scale_compensation": 100.0,
})
(SOURCE / "PR005_SERVICE_LOGISTICS_MANIFEST_v006.json").write_text(json.dumps(source_manifest, indent=2), encoding="utf-8")
(DERIVED / "PR005_SERVICE_LOGISTICS_UNREAL_DERIVED_MANIFEST_v007.json").write_text(json.dumps(derived_manifest, indent=2), encoding="utf-8")
print(json.dumps({"status": source_manifest["status"], "dimensions_mm": dimensions}, indent=2))
