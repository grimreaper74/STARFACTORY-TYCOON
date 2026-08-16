"""Author PR005 visual infill that reuses the retained v053 runtime safety cage.

Run with Blender 5.x. The source asset is dimensioned in metres. A separate
immutable-safe Unreal derivative multiplies local vertices by 100 to compensate
for the proven UE 5.8 Interchange 1/100 import behaviour on this asset family.
"""

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "SourceAssets/Candidate/PressShop/PR005/RuntimeCageInfill_v004"
DERIVED = ROOT / "SourceAssets/Candidate/PressShop/PR005/RuntimeCageInfill_UnrealDerived_v005"
SOURCE_EXPORTS = SOURCE / "Exports"
DERIVED_EXPORTS = DERIVED / "Exports"
ASSET = "SM_CA_MW_PR005_RuntimeCageInfill_Static_v004"
DERIVED_ASSET = "SM_CA_MW_PR005_RuntimeCageInfill_Static_v005"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def material(name, color, metallic=0.0, roughness=0.5):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.metallic = metallic
    mat.roughness = roughness
    return mat


def box(name, dimensions, location, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        modifier = obj.modifiers.new("FabricatedEdge", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    return obj


def raised_text(name, body, location, size, mat):
    bpy.ops.object.text_add(location=location, rotation=(math.radians(90.0), 0.0, math.radians(90.0)))
    obj = bpy.context.object
    obj.name = name
    obj.data.body = body
    obj.data.align_x = "CENTER"
    obj.data.align_y = "CENTER"
    obj.data.size = size
    obj.data.extrude = 0.012
    obj.data.bevel_depth = 0.003
    obj.data.materials.append(mat)
    bpy.ops.object.convert(target="MESH")
    return obj


def bounds_mm(obj):
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    low = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    high = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    return [round(v * 1000.0, 3) for v in low], [round(v * 1000.0, 3) for v in high], [round(v * 1000.0, 3) for v in high - low]


def export_selected(obj, path):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(
        filepath=str(path),
        use_selection=True,
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_UNITS",
        object_types={"MESH"},
        add_leaf_bones=False,
        bake_anim=False,
        mesh_smooth_type="FACE",
    )


if SOURCE.exists() or DERIVED.exists():
    raise RuntimeError("refusing to overwrite preserved RuntimeCageInfill v004/v005 source")
SOURCE_EXPORTS.mkdir(parents=True)
DERIVED_EXPORTS.mkdir(parents=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.length_unit = "METERS"
scene.unit_settings.scale_length = 1.0

charcoal = material("CA_MW_FoundryCharcoal", (0.045, 0.055, 0.058), metallic=0.72, roughness=0.34)
grey = material("CA_MW_ServiceGrey", (0.31, 0.34, 0.35), metallic=0.62, roughness=0.40)
glass = material("CA_MW_LaminatedInspectionGlass", (0.055, 0.12, 0.135), metallic=0.25, roughness=0.20)
green = material("CA_MW_CairnwellGreen", (0.015, 0.17, 0.105), metallic=0.30, roughness=0.36)
yellow = material("CA_MW_SafetyYellow", (0.92, 0.52, 0.015), metallic=0.34, roughness=0.32)
white = material("CA_MW_IdentityWhite", (0.82, 0.84, 0.82), metallic=0.12, roughness=0.35)

parts = []

# Exact retained v053 GuardingHMI bounds transformed to PR005 source-local metres:
# local X (across strip) -2.0706..+3.0106, local Y (flow) -3.57..+4.97,
# Z 0..2.415. Infill is intentionally inset and never becomes collision/runtime
# authority. Upstream Y < -1.0 remains the open guarded coil-loading bay.
service_x = -2.00
operator_x = 2.94
panel_centres = (-0.45, 0.60, 1.65, 2.70, 3.75, 4.45)
for side, x in (("Service", service_x), ("Operator", operator_x)):
    for index, y in enumerate(panel_centres, 1):
        # Preserve the inherited operator-gate opening at local Y 2.17..3.43.
        if side == "Operator" and 2.10 < y < 3.50:
            continue
        length = 0.94 if y < 4.4 else 0.68
        parts.append(box(f"{side}_KickPanel_{index:02d}", (0.055, length, 0.78), (x, y, 0.43), charcoal, 0.012))
        parts.append(box(f"{side}_InspectionPanel_{index:02d}", (0.038, length, 1.04), (x, y, 1.39), glass, 0.008))
        parts.append(box(f"{side}_TopRail_{index:02d}", (0.075, length, 0.10), (x, y, 1.96), yellow, 0.010))

# Process-bay roof only. It is inset from the cage, clear of the structural
# column at source-local X=-2.5 m and clear of the upstream maintenance gate.
roof_x_centre = 0.45
for index, y in enumerate((-0.48, 0.52, 1.52, 2.52, 3.52, 4.42), 1):
    length = 0.92 if index < 6 else 0.78
    parts.append(box(f"ProcessRoofCassette_{index:02d}", (4.76, length, 0.085), (roof_x_centre, y, 2.48), grey, 0.014))
    parts.append(box(f"ProcessRoofSeam_{index:02d}", (4.78, 0.045, 0.07), (roof_x_centre, y + length / 2.0, 2.525), charcoal, 0.006))

# Fabricated operator-side identity header attached to the proven cage line.
parts.append(box("OperatorIdentityFascia", (0.075, 2.70, 0.34), (2.975, 0.55, 2.19), green, 0.012))
parts.append(raised_text("Identity_Cairnwell", "CAIRNWELL AUTOMOTIVE", (3.016, 0.55, 2.255), 0.165, white))
parts.append(raised_text("Identity_Station", "MOORCROSS WORKS  |  PR-005", (3.017, 0.55, 2.115), 0.078, white))

# Small service-side removable access panels provide fabricated depth without
# inventing a new HMI, utility termination or operating mechanism.
for y in (0.05, 0.78, 1.51):
    parts.append(box(f"ServiceAccessCover_{y}", (0.075, 0.54, 0.42), (-2.035, y, 0.66), grey, 0.014))
    parts.append(box(f"ServiceAccessLatch_{y}", (0.025, 0.06, 0.08), (-2.078, y + 0.18, 0.66), yellow, 0.006))

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
asset["authority"] = "VISUAL_INFILL_ONLY_REUSES_RETAINED_V053_RUNTIME_GUARD"
asset["collision"] = "NO_COLLISION_NATIVE_V053_GUARD_REMAINS_AUTHORITY"
asset["navigation"] = "NO_NAV_EFFECT_NATIVE_V053_GUARD_REMAINS_AUTHORITY"
asset["world_placement"] = "DERIVED_FROM_RETAINED_V053_PR005_DATUM"
asset["planning_10400_vs_11500"] = "TBC_NOT_INVENTED"

source_min, source_max, source_dimensions = bounds_mm(asset)
blend_path = SOURCE / "PR005_RuntimeCageInfill_Candidate_v004.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
source_fbx = SOURCE_EXPORTS / f"{ASSET}.fbx"
export_selected(asset, source_fbx)

# Create a separate UE-specific derivative while preserving the authored source.
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(source_fbx), use_anim=False)
meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
if len(meshes) != 1:
    raise RuntimeError(f"expected one source mesh, found {len(meshes)}")
derived = meshes[0]
derived.data.transform(Matrix.Scale(100.0, 4))
derived.name = DERIVED_ASSET
derived.data.name = DERIVED_ASSET
derived_fbx = DERIVED_EXPORTS / f"{DERIVED_ASSET}.fbx"
export_selected(derived, derived_fbx)

generated = datetime.now(timezone.utc).isoformat()
source_manifest = {
    "$schema": "cairnwell/source/pr005-runtime-cage-infill-v004/v1",
    "generated_utc": generated,
    "status": "SOURCE_AUTHORED__VISUAL_INFILL_ONLY__UNREAL_IMPORT_AND_FIXED_CAMERA_GATES_REQUIRED__NOT_PROMOTED",
    "asset_name": ASSET,
    "fbx": f"Exports/{ASSET}.fbx",
    "blend": blend_path.name,
    "sha256": sha256(source_fbx),
    "blend_sha256": sha256(blend_path),
    "pivot_m": [0.0, 0.0, 0.0],
    "bounds_min_mm": source_min,
    "bounds_max_mm": source_max,
    "dimensions_mm": source_dimensions,
    "retained_v053_guard_local_bounds_m": {"min": [-2.0706, -3.57, 0.0], "max": [3.0106, 4.97, 2.415]},
    "structural_column_local_xy_m": [-2.5, 0.0],
    "column_clearance_basis": "infill minimum local X is greater than -2.10 m; retained column centre is -2.5 m with 0.225 m half width",
    "upstream_open_guarded_bay": "local Y < -1.0 m",
    "operator_gate_opening_preserved_local_y_m": [2.10, 3.50],
    "runtime_authority": "UNCHANGED_RETAINED_V053_GUARD_HMI_GATES_COLLISION_NAVIGATION",
    "world_placement": "DERIVED_FROM_RETAINED_V053_PR005_DATUM",
    "planning_10400_vs_11500": "TBC_NOT_INVENTED",
    "promotion_authorized": False,
}
(SOURCE / "PR005_RUNTIME_CAGE_INFILL_MANIFEST_v004.json").write_text(json.dumps(source_manifest, indent=2), encoding="utf-8")

derived_manifest = {
    "$schema": "cairnwell/source/pr005-runtime-cage-infill-unreal-derived-v005/v1",
    "generated_utc": generated,
    "status": "DERIVED_FBX_SCALE_COMPENSATION_ONLY__UNREAL_IMPORT_AUDIT_REQUIRED__NOT_PROMOTED",
    "source_candidate": "SourceAssets/Candidate/PressShop/PR005/RuntimeCageInfill_v004",
    "asset_name": DERIVED_ASSET,
    "fbx": f"Exports/{DERIVED_ASSET}.fbx",
    "sha256": sha256(derived_fbx),
    "source_fbx_sha256": sha256(source_fbx),
    "local_vertex_scale_compensation": 100.0,
    "expected_dimensions_mm": source_dimensions,
    "expected_bounds_min_mm": source_min,
    "expected_bounds_max_mm": source_max,
    "pivot_m": [0.0, 0.0, 0.0],
    "runtime_authority": "UNCHANGED_RETAINED_V053_GUARD_HMI_GATES_COLLISION_NAVIGATION",
    "promotion_authorized": False,
}
(DERIVED / "PR005_RUNTIME_CAGE_INFILL_UNREAL_DERIVED_MANIFEST_v005.json").write_text(json.dumps(derived_manifest, indent=2), encoding="utf-8")
print(json.dumps({"status": source_manifest["status"], "dimensions_mm": source_dimensions, "source": str(SOURCE), "derived": str(DERIVED)}, indent=2))
