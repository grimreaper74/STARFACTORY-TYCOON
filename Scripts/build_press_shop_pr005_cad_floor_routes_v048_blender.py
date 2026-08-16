"""Build one dimensioned, station-local PR-005 floor-route module in Blender 5.2.

Coordinates are metres in the PR-005 local frame.  The Unreal actor is placed
at the station datum (-4000, -2000, 0) cm with yaw -90 degrees.  The protected
walkway is exactly 11.5 x 1.5 m, matching the Pro operational plan.
"""

import json
import math
from pathlib import Path

import bpy


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT = ROOT / "SourceAssets/PR005/FloorRoutes/Candidate_v048"
FBX = OUT / "SM_PR005_CAD_FloorRoutes_Candidate_v048.fbx"
BLEND = OUT / "PR005_CAD_FloorRoutes_Candidate_v048.blend"
MANIFEST = OUT / "module_manifest.json"
OUT.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.system = "METRIC"
bpy.context.scene.unit_settings.scale_length = 1.0


def material(name, colour, metallic=0.0, roughness=0.78):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*colour, 1.0)
    mat.metallic = metallic
    mat.roughness = roughness
    return mat


GREEN = material("PR005_Route_ProtectedGreen", (0.045, 0.19, 0.105), roughness=0.84)
YELLOW = material("PR005_Route_SafetyYellow", (0.72, 0.39, 0.012), roughness=0.72)
RED = material("PR005_Route_MaintenanceRed", (0.40, 0.018, 0.012), roughness=0.76)
CYAN = material("PR005_Route_FlowCyan", (0.008, 0.30, 0.38), roughness=0.68)
WHITE = material("PR005_Route_LabelWhite", (0.68, 0.72, 0.70), roughness=0.82)
parts = []


def box(name, location, dimensions, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel > 0.0:
        modifier = obj.modifiers.new("PaintEdge", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
        modifier.limit_method = "ANGLE"
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    parts.append(obj)
    return obj


def text_mesh(name, body, location, size, mat):
    bpy.ops.object.text_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.body = body
    obj.data.align_x = "CENTER"
    obj.data.align_y = "CENTER"
    obj.data.size = size
    obj.data.extrude = 0.002
    obj.data.bevel_depth = 0.0008
    obj.data.bevel_resolution = 2
    obj.data.materials.append(mat)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    parts.append(obj)
    return obj


# Exact 11,500 x 1,500 mm protected north-side operator walkway.
box("PR005_ProtectedWalkway_11500x1500", (-6.45, 0.0, 0.034), (1.50, 11.50, 0.012), GREEN)
box("PR005_WalkwayEdge_Cell", (-5.70, 0.0, 0.043), (0.075, 11.50, 0.018), YELLOW, 0.004)
box("PR005_WalkwayEdge_Aisle", (-7.20, 0.0, 0.043), (0.075, 11.50, 0.018), YELLOW, 0.004)

# A restrained dashed maintenance boundary sits between protected pedestrians
# and the process cell.  It is intentionally separate from safety yellow.
for index, y in enumerate((-5.05, -3.95, -2.85, -1.75, -0.65, 0.45, 1.55, 2.65, 3.75, 4.85), 1):
    box(f"PR005_MaintenanceDash_{index:02d}", (-5.51, y, 0.055), (0.065, 0.70, 0.018), RED, 0.004)

# Material-flow line and chevron: station-local +Y becomes world +X.
box("PR005_FlowArrow_Shaft", (-5.22, 0.35, 0.055), (0.070, 7.70, 0.018), CYAN, 0.004)
# FBX's -Y forward conversion reverses this station-local axis in Unreal, so
# the source chevron belongs at negative local Y to point toward world +X.
head_a = box("PR005_FlowArrow_HeadA", (-5.22, -3.72, 0.055), (0.070, 0.85, 0.018), CYAN, 0.004)
head_a.rotation_euler[2] = 0.68
head_b = box("PR005_FlowArrow_HeadB", (-5.22, -3.72, 0.055), (0.070, 0.85, 0.018), CYAN, 0.004)
head_b.rotation_euler[2] = -0.68
bpy.context.view_layer.objects.active = head_a
bpy.ops.object.select_all(action="DESELECT")
head_a.select_set(True)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
bpy.ops.object.select_all(action="DESELECT")
head_b.select_set(True)
bpy.context.view_layer.objects.active = head_b
bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

# Embedded diegetic station title.  Cairnwell is the fictional corporation;
# Line Boss is deliberately absent because it is only the game's working title.
title = text_mesh("PR005_FloorTitle", "PR-005", (-6.45, -2.80, 0.052), 0.28, WHITE)
direction = text_mesh("PR005_WalkwayTitle", "PEDESTRIAN WALKWAY", (-6.45, 2.20, 0.052), 0.18, WHITE)
for obj in (title, direction):
    obj.rotation_euler[2] = math.pi
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

# Join to one reusable mesh while preserving the five semantic material slots.
bpy.ops.object.select_all(action="DESELECT")
for obj in parts:
    obj.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
module = bpy.context.object
module.name = "SM_PR005_CAD_FloorRoutes_Candidate_v048"
bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")

bpy.context.view_layer.objects.active = module
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=1.15192, island_margin=0.02)
bpy.ops.object.mode_set(mode="OBJECT")
module["asset_id"] = "LB-PR005-FLOOR-ROUTES-v048"
module["station"] = "PR-005"
module["walkway_length_mm"] = 11500
module["walkway_clearance_mm"] = 1500
module["station_local_datum"] = True
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
    "$schema": "line-boss/source/pr005-cad-floor-routes-candidate-v048/v1",
    "status": "DIMENSIONED_STATION_LOCAL_SOURCE_BUILT__UNREAL_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "blend": str(BLEND), "fbx": str(FBX), "object": module.name,
    "dimensions_m": dimensions,
    "station_datum_unreal_cm": [-4000.0, -2000.0, 0.0],
    "station_yaw_degrees": -90.0,
    "walkway_dimensions_mm": [11500, 1500],
    "material_slots": [slot.material.name for slot in module.material_slots],
    "source_object_count_before_join": len(parts),
    "collision_intent": "NoCollision",
    "navigation_intent": "can_ever_affect_navigation=false",
    "equipment_coordinates_modified": False,
    "promotion_authorized": False,
}
MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(f"LINE_BOSS_PR005_CAD_FLOOR_V048_SOURCE_PASS dimensions_m={dimensions} fbx={FBX}")
