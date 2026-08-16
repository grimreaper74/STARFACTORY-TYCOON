"""Add restrained identity and wear to the retained PR-005 service covers."""

import json
import math
from pathlib import Path

import bpy


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = ROOT / "SourceAssets/PR005/HydraulicRouting/Candidate_v051/PR005_HydraulicServiceCovers_Candidate_v051.blend"
OUT = ROOT / "SourceAssets/PR005/HydraulicRouting/Candidate_v052"
BLEND = OUT / "PR005_HydraulicServiceIdentity_Candidate_v052.blend"
FBX = OUT / "SM_PR005_HydraulicServiceIdentity_Candidate_v052.fbx"
MANIFEST = OUT / "module_manifest.json"
OUT.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
module = bpy.data.objects.get("SM_PR005_HydraulicServiceCovers_Candidate_v051")
if module is None:
    raise RuntimeError("Missing retained v051 service-cover source")


def material(name, colour, metallic, roughness):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*colour, 1.0)
    mat.metallic = metallic
    mat.roughness = roughness
    return mat


WHITE = material("PR005_ServiceCover_IdentityWhite", (0.66, 0.70, 0.68), 0.0, 0.80)
WEAR = material("PR005_ServiceCover_WearDark", (0.026, 0.018, 0.012), 0.42, 0.68)
parts = [module]


def text_mesh(name, body, location, size):
    bpy.ops.object.text_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.body = body
    obj.data.align_x = "CENTER"
    obj.data.align_y = "CENTER"
    obj.data.size = size
    obj.data.extrude = 0.0015
    obj.data.bevel_depth = 0.0005
    obj.data.bevel_resolution = 2
    obj.data.materials.append(WHITE)
    obj.rotation_euler[2] = math.pi
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    parts.append(obj)
    return obj


def vertical_text_mesh(name, body, location, size):
    bpy.ops.object.text_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.body = body
    obj.data.align_x = "CENTER"
    obj.data.align_y = "CENTER"
    obj.data.size = size
    obj.data.extrude = 0.0012
    obj.data.bevel_depth = 0.0004
    obj.data.bevel_resolution = 2
    obj.data.materials.append(WEAR)
    # Default text XY becomes plate YZ.  The retained station transform turns
    # local -X toward the gameplay-side camera, so the lettering must face -X.
    obj.rotation_euler = (math.pi / 2.0, 0.0, -math.pi / 2.0)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    parts.append(obj)
    return obj


def plate(name, location, dimensions):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(WHITE)
    modifier = obj.modifiers.new("PlateEdge", "BEVEL")
    modifier.width = 0.008
    modifier.segments = 3
    modifier.limit_method = "ANGLE"
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    parts.append(obj)
    return obj


def wear_mark(name, location, dimensions, yaw=0.0):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    obj.rotation_euler[2] = yaw
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    obj.data.materials.append(WEAR)
    modifier = obj.modifiers.new("WornEdge", "BEVEL")
    modifier.width = 0.002
    modifier.segments = 2
    modifier.limit_method = "ANGLE"
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    parts.append(obj)
    return obj


# Small top identities are readable in maintenance view without turning the
# floor service into an advertisement.  Cairnwell remains on the station HMI;
# these covers carry only functional plant wording.
plate("PR005_ServiceCover_IdentityPlate", (-4.345, -1.75, 0.220), (0.024, 0.72, 0.18))
vertical_text_mesh("PR005_ServiceCover_HydIdentity", "HYD SERVICE", (-4.360, -1.75, 0.245), 0.050)
vertical_text_mesh("PR005_ServiceCover_NoStepIdentity", "NO STEP", (-4.359, -1.75, 0.185), 0.040)

# Fixed, sparse edge-contact marks: no noisy procedural grime and no Surface
# Forge paint-chip texture on galvanised service metal.
wear_specs = [
    (-5.01, -3.42, 0.190, 0.11, 0.020, 0.16),
    (-4.49, -3.05, 0.190, 0.08, 0.018, -0.12),
    (-4.98, -2.72, 0.190, 0.09, 0.018, 0.08),
    (-4.52, -2.12, 0.190, 0.12, 0.020, -0.18),
    (-4.99, -1.72, 0.190, 0.07, 0.018, 0.10),
    (-4.50, -1.34, 0.190, 0.10, 0.018, -0.08),
    (-5.00, -0.72, 0.190, 0.12, 0.020, 0.14),
    (-4.51, -0.09, 0.190, 0.08, 0.018, -0.15),
]
for index, (x, y, z, dx, dy, yaw) in enumerate(wear_specs, 1):
    wear_mark(f"PR005_ServiceCover_Wear_{index:02d}", (x, y, z), (dx, dy, 0.004), yaw)

bpy.ops.object.select_all(action="DESELECT")
for obj in parts:
    obj.select_set(True)
bpy.context.view_layer.objects.active = module
bpy.ops.object.join()
module = bpy.context.object
module.name = "SM_PR005_HydraulicServiceIdentity_Candidate_v052"
bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")
bpy.context.view_layer.objects.active = module
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=1.15192, island_margin=0.02)
bpy.ops.object.mode_set(mode="OBJECT")
module["asset_id"] = "LB-PR005-HYD-SERVICE-IDENTITY-v052"
module["functional_identity"] = "HYD / NO STEP"
module["wear_mark_count"] = 8
module["line_boss_in_world_branding"] = False
module["source_status"] = "CANDIDATE_NOT_PROMOTED"

bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
bpy.ops.object.select_all(action="DESELECT")
module.select_set(True)
bpy.context.view_layer.objects.active = module
bpy.ops.export_scene.fbx(
    filepath=str(FBX), use_selection=True, object_types={"MESH"},
    apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
    mesh_smooth_type="FACE", use_mesh_modifiers=True,
    add_leaf_bones=False, bake_anim=False, axis_forward="-Y", axis_up="Z")

dimensions = [round(value, 6) for value in module.dimensions]
manifest = {
    "$schema": "line-boss/source/pr005-hydraulic-service-identity-candidate-v052/v1",
    "status": "FUNCTIONAL_IDENTITY_AND_RESTRAINED_WEAR_SOURCE_BUILT__UNREAL_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "source_blend": str(SOURCE), "blend": str(BLEND), "fbx": str(FBX),
    "object": module.name, "dimensions_m": dimensions,
    "functional_identity": ["HYD", "NO STEP"], "wear_mark_count": 8,
    "material_slots": [slot.material.name for slot in module.material_slots],
    "line_boss_in_world_branding": False,
    "promotion_authorized": False,
}
MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(f"LINE_BOSS_PR005_SERVICE_IDENTITY_V052_SOURCE_PASS dimensions_m={dimensions} fbx={FBX}")
