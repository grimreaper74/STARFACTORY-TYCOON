"""Rework v037 with a guarded near-side sheave cover for release-style readability."""

import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = ROOT / "SourceAssets/IndustrialKit/BridgeCrane/SupportHook/Candidate_v037/LB_Crane_SupportHookBlock_30T_Candidate_v037.blend"
OUT = ROOT / "SourceAssets/IndustrialKit/BridgeCrane/SupportHook/Candidate_v038"
FBX = OUT / "SM_LB_Crane_SupportHookBlock_30T_Candidate_v038.fbx"
BLEND = OUT / "LB_Crane_SupportHookBlock_30T_Candidate_v038.blend"
MANIFEST = OUT / "LB_Crane_SupportHookBlock_30T_Candidate_v038_manifest.json"
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
hook = bpy.data.objects.get("SM_LB_Crane_SupportHookBlock_30T_Candidate_v037")
if hook is None:
    raise RuntimeError("Missing v037 source hook object")
dark = bpy.data.materials.get("LB_Crane_DarkSteel")
steel = bpy.data.materials.get("LB_Crane_ExposedSteel")
yellow = bpy.data.materials.get("LB_Crane_RAL1023_Aged")
if any(value is None for value in (dark, steel, yellow)):
    raise RuntimeError("Missing v037 controlled materials")


def bevel(obj, width=0.012, segments=3):
    modifier = obj.modifiers.new("FabricationEdge", "BEVEL")
    modifier.width = width
    modifier.segments = segments
    modifier.limit_method = "ANGLE"
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    return obj


new_parts = []
bpy.ops.mesh.primitive_cube_add(location=(0.0, -0.292, 0.18))
cover = bpy.context.object
cover.name = "HookBlock_NearSheaveGuard"
cover.dimensions = (0.68, 0.045, 0.38)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
cover.data.materials.append(dark)
new_parts.append(bevel(cover, 0.018, 4))

# One restrained inspection cap replaces the bright exposed twin-sheave read.
start = Vector((0.0, -0.335, 0.18))
end = Vector((0.0, -0.300, 0.18))
delta = end - start
bpy.ops.mesh.primitive_cylinder_add(
    vertices=48, radius=0.105, depth=delta.length, location=(start + end) * 0.5)
cap = bpy.context.object
cap.name = "HookBlock_GuardInspectionCap"
cap.rotation_mode = "QUATERNION"
cap.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(delta.normalized())
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
cap.data.materials.append(steel)
new_parts.append(bevel(cap, 0.012, 3))

# Bolted yellow edge strips keep the block visually related to Cairnwell's crane fleet.
for x in (-0.315, 0.315):
    bpy.ops.mesh.primitive_cube_add(location=(x, -0.319, 0.18))
    strip = bpy.context.object
    strip.name = f"HookBlock_GuardEdge_{'L' if x < 0 else 'R'}"
    strip.dimensions = (0.045, 0.018, 0.34)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    strip.data.materials.append(yellow)
    new_parts.append(bevel(strip, 0.008, 3))

bpy.ops.object.select_all(action="DESELECT")
hook.select_set(True)
for obj in new_parts:
    obj.select_set(True)
bpy.context.view_layer.objects.active = hook
bpy.ops.object.join()
hook = bpy.context.object
hook.name = "SM_LB_Crane_SupportHookBlock_30T_Candidate_v038"
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=1.15192, island_margin=0.02)
bpy.ops.object.mode_set(mode="OBJECT")
hook["asset_id"] = "LB-CRANE-HOOKBLOCK-30T-v038"
hook["rated_load_t"] = 30.0
hook["role"] = "GENERAL_PURPOSE_MAINTENANCE_SUPPORT"
hook["master_coil_authority"] = False
hook["near_sheave_guard"] = True
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
    "$schema": "line-boss/source/support-hook-block-candidate-v038/v1",
    "status": "SOURCE_REWORKED__INDEPENDENT_IMPORT_AND_UNREAL_GATES_REQUIRED__NOT_PROMOTED",
    "source_blend": str(SOURCE), "blend": str(BLEND), "fbx": str(FBX),
    "object": hook.name, "dimensions_m": dimensions, "rated_load_t": 30.0,
    "role": "general-purpose maintenance support", "master_coil_authority": False,
    "near_sheave_guard": True,
    "material_slots": [slot.material.name for slot in hook.material_slots],
    "promotion_authorized": False,
}
MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(f"LINE_BOSS_SUPPORT_HOOK_V038_SOURCE_PASS dimensions_m={dimensions} fbx={FBX}")
