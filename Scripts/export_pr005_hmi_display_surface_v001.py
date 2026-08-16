"""Export the exact authored PR-005 live-display surface as an Unreal module."""

import json
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Brand\Candidate_v001\PR005_HMI\DisplaySurface_v001")
BLEND = ROOT / "LB_PR005_HMIDisplaySurface_Candidate_v001.blend"
FBX = ROOT / "SM_LB_PR005_HMIDisplaySurface_Candidate_v001.fbx"
MANIFEST = ROOT / "manifest.json"
SOURCE_NAME = "PR-005_HMILiveDisplaySurface"
STANDOFF_M = 0.008

ROOT.mkdir(parents=True, exist_ok=True)
source = bpy.data.objects.get(SOURCE_NAME)
source_blend = bpy.data.filepath
if source is None or source.type != "MESH":
    raise RuntimeError(f"Missing authored mesh {SOURCE_NAME}")

surface = source.copy()
surface.data = source.data.copy()
surface.parent = None
surface.name = "SM_LB_PR005_HMIDisplaySurface_Candidate_v001"
bpy.context.collection.objects.link(surface)
world_matrix = source.matrix_world.copy()
front_normal = -(world_matrix.to_3x3() @ Vector((1.0, 0.0, 0.0))).normalized()
surface.data.transform(Matrix.Translation(front_normal * STANDOFF_M) @ world_matrix)
surface.matrix_world = Matrix.Identity(4)

for obj in list(bpy.data.objects):
    if obj != surface:
        bpy.data.objects.remove(obj, do_unlink=True)

bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
bpy.ops.object.select_all(action="DESELECT")
surface.select_set(True)
bpy.context.view_layer.objects.active = surface
bpy.ops.export_scene.fbx(
    filepath=str(FBX), use_selection=True, object_types={"MESH"},
    apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
    axis_forward="-Y", axis_up="Z", use_mesh_modifiers=True,
    mesh_smooth_type="FACE", use_tspace=True, bake_anim=False,
    add_leaf_bones=False, path_mode="AUTO",
)

MANIFEST.write_text(json.dumps({
    "status": "CANDIDATE_NOT_PROMOTED",
    "source_object": SOURCE_NAME,
    "source_blend": source_blend,
    "export_fbx": str(FBX),
    "screen_size_mm": [340, 255],
    "authored_pitch_down_deg": 20,
    "standoff_mm": 8,
    "front_normal_blender": [round(value, 7) for value in front_normal],
    "coordinate_rule": "world-space Blender metres exported X-forward/Z-up; Unreal actor remains at origin",
}, indent=2), encoding="utf-8")
print(f"LINE_BOSS_PR005_HMI_DISPLAY_EXPORT_PASS fbx={FBX}")
