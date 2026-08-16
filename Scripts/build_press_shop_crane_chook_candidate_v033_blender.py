"""Build the dimensioned PR-004 40 t C-hook candidate v033 in Blender 5.2.

Coordinates are metres. Origin is the native hook datum; the padded bore arm
centre is exactly 0.590 m below it, matching ALBBridgeCraneController.
"""

import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT = ROOT / "SourceAssets/IndustrialKit/BridgeCrane/CHook/Candidate_v033"
FBX = OUT / "SM_LB_Crane_CHook_Candidate_v033.fbx"
BLEND = OUT / "LB_Crane_CHook_Candidate_v033.blend"
MANIFEST = OUT / "LB_Crane_CHook_Candidate_v033_manifest.json"
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.system = "METRIC"
bpy.context.scene.unit_settings.scale_length = 1.0


def material(name, color, metallic, roughness):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.metallic = metallic
    mat.roughness = roughness
    return mat


YELLOW = material("LB_Crane_RAL1023_Aged", (0.56, 0.29, 0.008), 0.35, 0.46)
DARK = material("LB_Crane_DarkSteel", (0.018, 0.024, 0.031), 0.82, 0.33)
STEEL = material("LB_Crane_ExposedSteel", (0.25, 0.29, 0.33), 1.0, 0.28)
RUBBER = material("LB_Crane_BorePad", (0.012, 0.014, 0.016), 0.0, 0.72)
parts = []


def bevel(obj, width=0.025, segments=3):
    modifier = obj.modifiers.new("FabricationEdge", "BEVEL")
    modifier.width = width
    modifier.segments = segments
    modifier.limit_method = "ANGLE"
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    for polygon in obj.data.polygons:
        polygon.use_smooth = False
    return obj


def prism_from_xz(name, points, depth, mat):
    count = len(points)
    vertices = [(x, -depth / 2, z) for x, z in points] + [(x, depth / 2, z) for x, z in points]
    faces = [tuple(range(count - 1, -1, -1)), tuple(range(count, count * 2))]
    for index in range(count):
        nxt = (index + 1) % count
        faces.append((index, nxt, count + nxt, count + index))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    parts.append(bevel(obj, 0.032, 4))
    return obj


def cube(name, location, dimensions, mat, bevel_width=0.02):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    parts.append(bevel(obj, bevel_width, 3))
    return obj


def cylinder_between(name, start, end, radius, mat, vertices=48):
    start, end = Vector(start), Vector(end)
    delta = end - start
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=delta.length,
                                       location=(start + end) * 0.5)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(delta.normalized())
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    parts.append(bevel(obj, min(radius * 0.16, 0.018), 3))
    return obj


# Forged C profile: 1.40 m reach, 0.30 m plate depth, 1.46 m total height.
profile = [
    (-0.42, 0.54), (-0.10, 0.67), (0.18, 0.60), (0.38, 0.40),
    (0.43, 0.14), (0.33, -0.08), (0.10, -0.25), (-0.07, -0.29),
    (-0.07, -0.43), (1.72, -0.43), (1.88, -0.53), (1.88, -0.63),
    (1.74, -0.70), (-0.20, -0.70), (-0.39, -0.57), (-0.52, -0.24),
    (-0.52, 0.17),
]
prism_from_xz("CHook_ForgedBody", profile, 0.30, YELLOW)

# Replaceable padded arm is centred exactly at native load-centre offset.
cylinder_between("CHook_BoreArmCore", (-0.04, 0.0, -0.59), (1.86, 0.0, -0.59), 0.135, STEEL)
cylinder_between("CHook_BoreArmPad", (0.06, 0.0, -0.59), (1.72, 0.0, -0.59), 0.165, RUBBER)
cylinder_between("CHook_BoreArmNose", (1.72, 0.0, -0.59), (1.90, 0.0, -0.59), 0.145, YELLOW)

# Compact suspension head: twin cheek plates, sheave, pins and lifting eye.
for y in (-0.19, 0.19):
    cube(f"CHook_HeadCheek_{'L' if y < 0 else 'R'}", (-0.18, y, 0.61),
         (0.48, 0.055, 0.46), DARK, 0.018)
cylinder_between("CHook_HeadSheave", (-0.18, -0.22, 0.63), (-0.18, 0.22, 0.63), 0.17, STEEL)
cylinder_between("CHook_HeadPin", (-0.18, -0.25, 0.63), (-0.18, 0.25, 0.63), 0.055, DARK)
cube("CHook_HeadCrown", (-0.18, 0.0, 0.86), (0.52, 0.42, 0.12), YELLOW, 0.025)
bpy.ops.mesh.primitive_torus_add(major_radius=0.15, minor_radius=0.052,
                                 major_segments=64, minor_segments=16,
                                 location=(-0.18, 0.0, 1.06), rotation=(1.57079632679, 0, 0))
eye = bpy.context.object
eye.name = "CHook_LiftingEye"
eye.data.materials.append(STEEL)
parts.append(eye)

# Wear plates and load-rating plaque are separate geometry/material regions.
cube("CHook_HeelWearPlate", (-0.34, 0.0, -0.48), (0.23, 0.32, 0.065), STEEL, 0.012)
cube("CHook_SWLPlate", (-0.515, -0.158, 0.16), (0.012, 0.30, 0.18), DARK, 0.008)

for obj in parts:
    obj.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
hook = bpy.context.object
hook.name = "SM_LB_Crane_CHook_Candidate_v033"
# Explicit UVs give Unreal a stable MikkTSpace basis and remove the tangent
# warnings produced by a geometry-only FBX.
bpy.context.view_layer.objects.active = hook
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=1.15192, island_margin=0.02)
bpy.ops.object.mode_set(mode="OBJECT")
hook["asset_id"] = "LB-CRANE-CH-40T-v033"
hook["rated_load_t"] = 40.0
hook["hook_datum_m"] = 0.0
hook["bore_arm_centre_below_datum_m"] = 0.59
hook["overall_reach_m"] = 2.42
hook["body_to_load_centre_m"] = 1.50
hook["source_status"] = "CANDIDATE_NOT_PROMOTED"

bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
bpy.ops.object.select_all(action="DESELECT")
hook.select_set(True)
bpy.context.view_layer.objects.active = hook
bpy.ops.export_scene.fbx(filepath=str(FBX), use_selection=True, object_types={"MESH"},
                         apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
                         mesh_smooth_type="FACE", use_mesh_modifiers=True,
                         add_leaf_bones=False, bake_anim=False, axis_forward="-Y", axis_up="Z")

dimensions = [round(value, 6) for value in hook.dimensions]
manifest = {
    "$schema": "line-boss/source/bridge-crane-chook-candidate-v033/v1",
    "status": "SOURCE_BUILT__INDEPENDENT_IMPORT_AND_UNREAL_GATES_REQUIRED__NOT_PROMOTED",
    "blend": str(BLEND), "fbx": str(FBX), "object": hook.name,
    "dimensions_m": dimensions, "rated_load_t": 40.0,
    "hook_datum_m": 0.0, "bore_arm_centre_below_datum_m": 0.59,
    "body_to_load_centre_m": 1.50,
    "material_slots": [slot.material.name for slot in hook.material_slots],
    "promotion_authorized": False,
}
MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(f"LINE_BOSS_CRANE_CHOOK_V033_SOURCE_PASS dimensions_m={dimensions} fbx={FBX}")
