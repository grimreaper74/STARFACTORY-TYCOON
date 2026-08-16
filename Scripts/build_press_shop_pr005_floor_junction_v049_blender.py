"""Add a dimensioned factory cross-aisle junction to retained PR-005 v048."""

import json
from pathlib import Path

import bpy


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = ROOT / "SourceAssets/PR005/FloorRoutes/Candidate_v048/PR005_CAD_FloorRoutes_Candidate_v048.blend"
OUT = ROOT / "SourceAssets/PR005/FloorRoutes/Candidate_v049"
BLEND = OUT / "PR005_CAD_FloorRoutes_Junction_Candidate_v049.blend"
FBX = OUT / "SM_PR005_CAD_FloorRoutes_Junction_Candidate_v049.fbx"
MANIFEST = OUT / "module_manifest.json"
OUT.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
module = bpy.data.objects.get("SM_PR005_CAD_FloorRoutes_Candidate_v048")
white = bpy.data.materials.get("PR005_Route_LabelWhite")
yellow = bpy.data.materials.get("PR005_Route_SafetyYellow")
if module is None or white is None or yellow is None:
    raise RuntimeError("Missing retained v048 route module or semantic materials")

parts = [module]


def box(name, location, dimensions, material):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    modifier = obj.modifiers.new("PaintEdge", "BEVEL")
    modifier.width = 0.004
    modifier.segments = 2
    modifier.limit_method = "ANGLE"
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    parts.append(obj)
    return obj


# The pale factory cross-aisle intersects the west end of PR-005 at world
# X≈-4420 cm.  With the proven FBX/datum conversion this is local Y=+4.20 m.
# Eight 120 mm bars form a 1.80 m-long marked crossing within the exact 1.50 m
# protected walkway; yellow thresholds announce the transition at both sides.
bar_centres = (3.42, 3.64, 3.86, 4.08, 4.30, 4.52, 4.74, 4.96)
for index, y in enumerate(bar_centres, 1):
    box(f"PR005_CrossAisleJunctionBar_{index:02d}", (-6.45, y, 0.064), (1.26, 0.12, 0.018), white)
for suffix, y in (("West", 3.25), ("East", 5.13)):
    box(f"PR005_CrossAisleJunctionThreshold_{suffix}", (-6.45, y, 0.064), (1.48, 0.060, 0.018), yellow)

bpy.ops.object.select_all(action="DESELECT")
for obj in parts:
    obj.select_set(True)
bpy.context.view_layer.objects.active = module
bpy.ops.object.join()
module = bpy.context.object
module.name = "SM_PR005_CAD_FloorRoutes_Junction_Candidate_v049"
bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")
bpy.context.view_layer.objects.active = module
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=1.15192, island_margin=0.02)
bpy.ops.object.mode_set(mode="OBJECT")
module["asset_id"] = "LB-PR005-FLOOR-ROUTES-JUNCTION-v049"
module["station"] = "PR-005"
module["walkway_length_mm"] = 11500
module["walkway_clearance_mm"] = 1500
module["crossing_length_mm"] = 1800
module["crossing_clear_width_mm"] = 1260
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
    "$schema": "line-boss/source/pr005-floor-routes-junction-candidate-v049/v1",
    "status": "DIMENSIONED_CROSS_AISLE_JUNCTION_SOURCE_BUILT__UNREAL_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "source_blend": str(SOURCE), "blend": str(BLEND), "fbx": str(FBX),
    "object": module.name, "dimensions_m": dimensions,
    "walkway_dimensions_mm": [11500, 1500],
    "crossing_dimensions_mm": [1800, 1260],
    "crossing_bar_count": 8, "threshold_count": 2,
    "material_slots": [slot.material.name for slot in module.material_slots],
    "collision_intent": "NoCollision",
    "navigation_intent": "can_ever_affect_navigation=false",
    "equipment_coordinates_modified": False,
    "promotion_authorized": False,
}
MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(f"LINE_BOSS_PR005_FLOOR_JUNCTION_V049_SOURCE_PASS dimensions_m={dimensions} fbx={FBX}")
