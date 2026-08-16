"""Build removable tread covers for the straight PR-005 twin-hose run."""

import json
from pathlib import Path

import bpy


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT = ROOT / "SourceAssets/PR005/HydraulicRouting/Candidate_v051"
BLEND = OUT / "PR005_HydraulicServiceCovers_Candidate_v051.blend"
FBX = OUT / "SM_PR005_HydraulicServiceCovers_Candidate_v051.fbx"
MANIFEST = OUT / "module_manifest.json"
OUT.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.system = "METRIC"
bpy.context.scene.unit_settings.scale_length = 1.0


def material(name, colour, metallic, roughness):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*colour, 1.0)
    mat.metallic = metallic
    mat.roughness = roughness
    return mat


GALV = material("PR005_ServiceCover_Galvanised", (0.30, 0.34, 0.35), 0.78, 0.46)
GRIP = material("PR005_ServiceCover_AntiSlip", (0.025, 0.030, 0.033), 0.32, 0.72)
YELLOW = material("PR005_ServiceCover_SafetyYellow", (0.70, 0.35, 0.008), 0.18, 0.70)
parts = []


def box(name, location, dimensions, mat, bevel=0.008):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel > 0.0:
        modifier = obj.modifiers.new("FabricationEdge", "BEVEL")
        modifier.width = bevel
        modifier.segments = 3
        modifier.limit_method = "ANGLE"
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    parts.append(obj)
    return obj


# Proven hydraulic source coordinates: twin hoses follow X=-4.66/-4.82 m.
# Cover only the straight Y=-3.49..-0.01 m run.  The HPU flex loop at the
# negative-Y end and cell/service access at positive Y remain deliberately open.
panel_centres = (-3.15, -2.45, -1.75, -1.05, -0.35)
for panel_index, y in enumerate(panel_centres, 1):
    box(f"PR005_ServiceCover_Panel_{panel_index:02d}", (-4.74, y, 0.155),
        (0.68, 0.64, 0.050), GALV, 0.012)
    box(f"PR005_ServiceCover_Panel_{panel_index:02d}_GripPad",
        (-4.74, y, 0.184), (0.48, 0.48, 0.008), GRIP, 0.004)

# Low yellow retainers prevent a cover from being shifted sideways while still
# allowing maintenance removal from above.
for suffix, x in (("CellSide", -5.105), ("AisleSide", -4.375)):
    box(f"PR005_ServiceCover_Retainer_{suffix}", (x, -1.75, 0.080),
        (0.045, 3.55, 0.070), YELLOW, 0.010)

bpy.ops.object.select_all(action="DESELECT")
for obj in parts:
    obj.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
module = bpy.context.object
module.name = "SM_PR005_HydraulicServiceCovers_Candidate_v051"
bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")
bpy.context.view_layer.objects.active = module
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=1.15192, island_margin=0.02)
bpy.ops.object.mode_set(mode="OBJECT")
module["asset_id"] = "LB-PR005-HYD-SERVICE-COVERS-v051"
module["panel_count"] = 5
module["covered_run_length_mm"] = 3480
module["cover_width_mm"] = 680
module["removable_from_above"] = True
module["flexible_end_zones_preserved"] = True
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
    "$schema": "line-boss/source/pr005-hydraulic-service-covers-candidate-v051/v1",
    "status": "DIMENSIONED_REMOVABLE_SERVICE_COVER_SOURCE_BUILT__UNREAL_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "blend": str(BLEND), "fbx": str(FBX), "object": module.name,
    "dimensions_m": dimensions, "panel_count": 5,
    "covered_run_dimensions_mm": [3480, 680],
    "panel_dimensions_mm": [640, 680, 50],
    "grip_pads_per_panel": 1, "side_retainer_count": 2,
    "flexible_end_zones_preserved": True,
    "material_slots": [slot.material.name for slot in module.material_slots],
    "promotion_authorized": False,
}
MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(f"LINE_BOSS_PR005_SERVICE_COVERS_V051_SOURCE_PASS dimensions_m={dimensions} fbx={FBX}")
