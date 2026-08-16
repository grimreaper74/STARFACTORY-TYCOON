import bpy
import json
from pathlib import Path

ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = ROOT / "SourceAssets/Candidate/PressShop/PR004_FilmDepack/Assembly_v20260810/Cairnwell_PR004_CradleWinderFit_v990.blend"
OUT_DIR = ROOT / "SourceAssets/Candidate/PressShop/PR004_FilmDepack/Assembly_v20260810/Runtime_v991"
OUT_BLEND = OUT_DIR / "Cairnwell_PR004_CradleWinder_Runtime_v991.blend"
OUT_FBX = OUT_DIR / "SM_Cairnwell_PR004_CradleWinder_Runtime_v991.fbx"
AUDIT = ROOT / "Saved/Audits/PressShopIntegration/pr004_cradle_winder_runtime_export_v991.json"

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
for obj in list(bpy.data.objects):
    if obj.name.startswith("FIT_COIL_"):
        bpy.data.objects.remove(obj, do_unlink=True)

meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
source_triangles = sum(sum(len(poly.vertices) - 2 for poly in obj.data.polygons) for obj in meshes)

for obj in meshes:
    triangles = sum(len(poly.vertices) - 2 for poly in obj.data.polygons)
    if triangles < 2500:
        continue
    modifier = obj.modifiers.new("RuntimeSilhouetteReduction", "DECIMATE")
    modifier.decimate_type = "COLLAPSE"
    modifier.ratio = 0.12
    modifier.use_collapse_triangulate = True
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    obj.select_set(False)

runtime_triangles = sum(sum(len(poly.vertices) - 2 for poly in obj.data.polygons) for obj in meshes)
OUT_DIR.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))

bpy.ops.object.select_all(action="DESELECT")
for obj in meshes:
    obj.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.export_scene.fbx(
    filepath=str(OUT_FBX),
    use_selection=True,
    object_types={"MESH"},
    axis_forward="-Z",
    axis_up="Y",
    apply_unit_scale=True,
    apply_scale_options="FBX_SCALE_UNITS",
    use_space_transform=True,
    bake_space_transform=False,
    bake_anim=False,
    use_mesh_modifiers=True,
    mesh_smooth_type="FACE",
    path_mode="AUTO",
)

payload = {
    "status": "PASS__BLENDER_RUNTIME_DERIVATIVE_EXPORTED__UNREAL_IMPORT_PENDING",
    "source": str(SOURCE),
    "runtime_blend": str(OUT_BLEND),
    "fbx": str(OUT_FBX),
    "mesh_objects": len(meshes),
    "source_triangles": source_triangles,
    "runtime_triangles": runtime_triangles,
    "triangle_ratio": round(runtime_triangles / source_triangles, 6),
    "coil_excluded": True,
    "full_detail_masters_preserved": True,
    "meshy_credits_used": 0,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print("LINE_BOSS_PR004_CRADLE_WINDER_RUNTIME_V991", source_triangles, runtime_triangles)
