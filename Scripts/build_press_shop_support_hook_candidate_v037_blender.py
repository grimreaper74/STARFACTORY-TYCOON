"""Build a dimensioned 30 t general-purpose maintenance hook block in Blender 5.2.

Coordinates are metres. The actor datum is the lower-block centre used by the
existing CR-30-01 controller; the upper suspension pin aligns with the retained
short hook link, while the forged hook hangs below the datum.
"""

import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT = ROOT / "SourceAssets/IndustrialKit/BridgeCrane/SupportHook/Candidate_v037"
FBX = OUT / "SM_LB_Crane_SupportHookBlock_30T_Candidate_v037.fbx"
BLEND = OUT / "LB_Crane_SupportHookBlock_30T_Candidate_v037.blend"
MANIFEST = OUT / "LB_Crane_SupportHookBlock_30T_Candidate_v037_manifest.json"
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


YELLOW = material("LB_Crane_RAL1023_Aged", (0.56, 0.29, 0.008), 0.35, 0.48)
DARK = material("LB_Crane_DarkSteel", (0.018, 0.024, 0.031), 0.82, 0.34)
STEEL = material("LB_Crane_ExposedSteel", (0.25, 0.29, 0.33), 1.0, 0.28)
RED = material("LB_Crane_SafetyLatch", (0.48, 0.025, 0.012), 0.35, 0.42)
parts = []


def bevel(obj, width=0.018, segments=3):
    modifier = obj.modifiers.new("FabricationEdge", "BEVEL")
    modifier.width = width
    modifier.segments = segments
    modifier.limit_method = "ANGLE"
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    return obj


def cube(name, location, dimensions, mat, bevel_width=0.018):
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
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=radius, depth=delta.length,
        location=(start + end) * 0.5)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(delta.normalized())
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    parts.append(bevel(obj, min(radius * 0.14, 0.014), 3))
    return obj


def prism_from_xz(name, points, depth, mat):
    count = len(points)
    vertices = ([(x, -depth / 2, z) for x, z in points]
                + [(x, depth / 2, z) for x, z in points])
    faces = [tuple(range(count - 1, -1, -1)), tuple(range(count, count * 2))]
    for index in range(count):
        nxt = (index + 1) % count
        faces.append((index, nxt, count + nxt, count + index))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    parts.append(bevel(obj, 0.022, 4))
    return obj


# Twin fabricated cheek plates around two 30 t reeving sheaves.
for y in (-0.235, 0.235):
    cube(f"HookBlock_Cheek_{'L' if y < 0 else 'R'}", (0.0, y, 0.18),
         (0.78, 0.055, 0.58), YELLOW, 0.025)
for x in (-0.19, 0.19):
    cylinder_between(f"HookBlock_Sheave_{'A' if x < 0 else 'B'}",
                     (x, -0.27, 0.22), (x, 0.27, 0.22), 0.19, STEEL)
    cylinder_between(f"HookBlock_Pin_{'A' if x < 0 else 'B'}",
                     (x, -0.31, 0.22), (x, 0.31, 0.22), 0.055, DARK)
cube("HookBlock_Crown", (0.0, 0.0, 0.50), (0.58, 0.50, 0.16), DARK, 0.025)
cylinder_between("HookBlock_SuspensionPin", (0.0, -0.31, 0.58),
                 (0.0, 0.31, 0.58), 0.075, STEEL)

# Swivel and thrust-bearing stack between the sheave block and forged hook.
cylinder_between("HookBlock_SwivelUpper", (0.0, 0.0, 0.00),
                 (0.0, 0.0, -0.18), 0.14, DARK)
cylinder_between("HookBlock_SwivelCollar", (0.0, 0.0, -0.16),
                 (0.0, 0.0, -0.27), 0.19, YELLOW)
cylinder_between("HookBlock_HookShank", (0.0, 0.0, -0.22),
                 (0.0, 0.0, -0.42), 0.105, STEEL)

# Closed forged profile with a clear throat. This is a conventional lifting
# hook, not a C-hook, so CR-30-01 no longer reads as a second coil authority.
hook_profile = [
    (-0.11, -0.34), (0.11, -0.34), (0.13, -0.62),
    (0.18, -0.78), (0.30, -0.91), (0.47, -0.96),
    (0.63, -0.90), (0.73, -0.77), (0.76, -0.62),
    (0.70, -0.48), (0.57, -0.39), (0.43, -0.36),
    (0.43, -0.51), (0.53, -0.55), (0.57, -0.64),
    (0.53, -0.73), (0.44, -0.79), (0.34, -0.77),
    (0.27, -0.68), (0.23, -0.55), (0.21, -0.34),
]
prism_from_xz("HookBlock_ForgedHook", hook_profile, 0.23, YELLOW)
cylinder_between("HookBlock_SafetyLatch", (0.16, -0.13, -0.47),
                 (0.47, -0.13, -0.52), 0.035, RED, vertices=32)
cylinder_between("HookBlock_LatchPin", (0.16, -0.16, -0.47),
                 (0.16, 0.16, -0.47), 0.042, STEEL, vertices=32)

# Replaceable bumper corners and a restrained SWL plaque region.
for x in (-0.34, 0.34):
    cube(f"HookBlock_Bumper_{'L' if x < 0 else 'R'}", (x, 0.0, -0.04),
         (0.10, 0.54, 0.14), DARK, 0.015)
cube("HookBlock_SWLPlate", (-0.405, -0.265, 0.18), (0.018, 0.24, 0.18), DARK, 0.008)

for obj in parts:
    obj.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
hook = bpy.context.object
hook.name = "SM_LB_Crane_SupportHookBlock_30T_Candidate_v037"
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=1.15192, island_margin=0.02)
bpy.ops.object.mode_set(mode="OBJECT")
hook["asset_id"] = "LB-CRANE-HOOKBLOCK-30T-v037"
hook["rated_load_t"] = 30.0
hook["role"] = "GENERAL_PURPOSE_MAINTENANCE_SUPPORT"
hook["master_coil_authority"] = False
hook["source_status"] = "CANDIDATE_NOT_PROMOTED"

bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
bpy.ops.object.select_all(action="DESELECT")
hook.select_set(True)
bpy.context.view_layer.objects.active = hook
bpy.ops.export_scene.fbx(
    filepath=str(FBX), use_selection=True, object_types={"MESH"},
    apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
    mesh_smooth_type="FACE", use_mesh_modifiers=True,
    add_leaf_bones=False, bake_anim=False, axis_forward="-Y", axis_up="Z")

dimensions = [round(value, 6) for value in hook.dimensions]
manifest = {
    "$schema": "line-boss/source/support-hook-block-candidate-v037/v1",
    "status": "SOURCE_BUILT__INDEPENDENT_IMPORT_AND_UNREAL_GATES_REQUIRED__NOT_PROMOTED",
    "blend": str(BLEND), "fbx": str(FBX), "object": hook.name,
    "dimensions_m": dimensions, "rated_load_t": 30.0,
    "role": "general-purpose maintenance support",
    "master_coil_authority": False,
    "material_slots": [slot.material.name for slot in hook.material_slots],
    "promotion_authorized": False,
}
MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(f"LINE_BOSS_SUPPORT_HOOK_V037_SOURCE_PASS dimensions_m={dimensions} fbx={FBX}")
