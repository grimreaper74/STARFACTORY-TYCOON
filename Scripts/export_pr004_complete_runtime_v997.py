"""Create the single-mesh PR004 runtime visual and reusable empty coil saddle."""
import bpy
import json
from pathlib import Path
from mathutils import Vector

ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
CELL_SOURCE = ROOT / "SourceAssets/Candidate/PressShop/PR004_FilmDepack/Assembly_v20260810/Cairnwell_PR004_CompleteCell_v996.blend"
SADDLE_SOURCE = ROOT / "SourceAssets/Candidate/PressShop/PR004_FilmDepack/BareCoilOutputSaddle_v20260810/Cleaned/Cairnwell_BareCoilOutputSaddle_Controlled_v994.blend"
OUT = ROOT / "SourceAssets/Candidate/PressShop/PR004_FilmDepack/Runtime_v997"
AUDIT = ROOT / "Saved/Audits/PressShopIntegration/pr004_complete_runtime_export_v997.json"


def triangles(obj):
    return sum(max(0, len(poly.vertices) - 2) for poly in obj.data.polygons)


def world_bounds(objects):
    points = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    return low, high


def delete_matching(parts):
    removed = []
    for obj in list(bpy.context.scene.objects):
        if any(part in obj.name for part in parts):
            removed.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)
    return removed


def reduce_and_join(name):
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    bpy.context.view_layer.update()
    source_tris = sum(triangles(obj) for obj in meshes)
    for obj in meshes:
        count = triangles(obj)
        if count < 2500:
            continue
        modifier = obj.modifiers.new("RuntimeSilhouetteReduction", "DECIMATE")
        modifier.decimate_type = "COLLAPSE"
        modifier.ratio = 0.12
        modifier.use_collapse_triangulate = True
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        obj.select_set(False)
    bpy.context.view_layer.update()
    reduced_tris = sum(triangles(obj) for obj in meshes)
    low, high = world_bounds(meshes)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    joined = bpy.context.view_layer.objects.active
    joined.name = name
    joined.data.name = name
    return joined, source_tris, reduced_tris, low, high


def export_asset(source, name, blend_name, fbx_name, remove_parts=()):
    bpy.ops.wm.open_mainfile(filepath=str(source))
    removed = delete_matching(remove_parts)
    joined, source_tris, runtime_tris, low, high = reduce_and_join(name)
    # Runtime pivots are floor-seated and centred in XY for predictable placement.
    centre = Vector(((low.x + high.x) * 0.5, (low.y + high.y) * 0.5, low.z))
    joined.location -= centre
    bpy.context.view_layer.update()
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    OUT.mkdir(parents=True, exist_ok=True)
    blend_path = OUT / blend_name
    fbx_path = OUT / fbx_name
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    bpy.ops.object.select_all(action="DESELECT")
    joined.select_set(True)
    bpy.context.view_layer.objects.active = joined
    bpy.ops.export_scene.fbx(
        filepath=str(fbx_path), use_selection=True, object_types={"MESH"},
        axis_forward="-Z", axis_up="Y", apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_UNITS", use_space_transform=True,
        bake_space_transform=False, bake_anim=False, use_mesh_modifiers=True,
        mesh_smooth_type="FACE", path_mode="AUTO")
    return {
        "source": str(source), "runtime_blend": str(blend_path), "fbx": str(fbx_path),
        "source_triangles": source_tris, "runtime_triangles": runtime_tris,
        "triangle_ratio": round(runtime_tris / source_tris, 6),
        "source_envelope_m": [round(value, 6) for value in high - low],
        "floor_seated_xy_centred": True, "single_static_mesh": True,
        "removed_load_objects": removed,
    }


cell = export_asset(
    CELL_SOURCE, "SM_Cairnwell_PR004_CompleteCell_Runtime_v997",
    "Cairnwell_PR004_CompleteCell_Runtime_v997.blend",
    "SM_Cairnwell_PR004_CompleteCell_Runtime_v997.fbx",
    ("AB_FIT_COIL_", "D_OUTPUT_FIT_"))
saddle = export_asset(
    SADDLE_SOURCE, "SM_Cairnwell_AdjustableCoilSaddle_Runtime_v997",
    "Cairnwell_AdjustableCoilSaddle_Runtime_v997.blend",
    "SM_Cairnwell_AdjustableCoilSaddle_Runtime_v997.fbx")

payload = {
    "status": "PASS__BLENDER_RUNTIME_DERIVATIVES_EXPORTED__UNREAL_IMPORT_PENDING",
    "pr004_complete_cell": cell,
    "player_placeable_empty_coil_saddle": saddle,
    "full_detail_split_masters_preserved": True,
    "normal_unloading_method": "autonomous heavy coil-handler AGV; crane retired from normal flow",
    "meshy_credits_used": 0,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print("LINE_BOSS_PR004_RUNTIME_V997", cell["runtime_triangles"], saddle["runtime_triangles"])
