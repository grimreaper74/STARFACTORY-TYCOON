import bpy
import json
import os

SOURCE = r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\WeldShop\PanelStillage_ThreeHigh_Intake_v001\Authority\GenerateTextureBranch\Meshy_AI_Industrial_Adjustable_0812070022_texture.blend"
OUT_DIR = r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\WeldShop\PanelStillage_RuntimeDerivation_v001"
BLEND_OUT = os.path.join(OUT_DIR, "LB_PanelStillage_Runtime_v001.blend")
FBX_OUT = os.path.join(OUT_DIR, "Exports", "SM_LB_PanelStillage_Runtime_v001.fbx")
GLB_OUT = os.path.join(OUT_DIR, "Exports", "SM_LB_PanelStillage_Runtime_v001.glb")
REPORT_OUT = os.path.join(OUT_DIR, "Audit", "derivation_report_v001.json")

os.makedirs(os.path.dirname(FBX_OUT), exist_ok=True)
os.makedirs(os.path.dirname(REPORT_OUT), exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=SOURCE)

# The coherent generate/texture branch is one whole stillage.  Preserve its UVs,
# packed PBR material and dimensions; reduce only render density for a repeated
# three-high storage visual.  The runtime actor keeps collision disabled.
objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
if len(objects) != 1:
    raise RuntimeError(f"Expected exactly one coherent stillage mesh, found {len(objects)}")
obj = objects[0]
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
for other in bpy.context.selected_objects:
    if other != obj:
        other.select_set(False)

source_tris = sum(len(poly.vertices) - 2 for poly in obj.data.polygons)
decimate = obj.modifiers.new(name="Runtime_LOD0_Decimate", type='DECIMATE')
decimate.ratio = 0.005
decimate.decimate_type = 'COLLAPSE'
decimate.use_collapse_triangulate = True
bpy.ops.object.modifier_apply(modifier=decimate.name)

obj.name = "SM_LB_PanelStillage_Runtime_v001"
obj.data.name = "SM_LB_PanelStillage_Runtime_v001"
obj.location = (0.0, 0.0, 0.0)
obj.rotation_euler = (0.0, 0.0, 0.0)

runtime_tris = sum(len(poly.vertices) - 2 for poly in obj.data.polygons)
dimensions = [float(value) for value in obj.dimensions]

bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUT)
bpy.ops.export_scene.fbx(
    filepath=FBX_OUT,
    use_selection=True,
    apply_unit_scale=True,
    bake_space_transform=False,
    object_types={'MESH'},
    mesh_smooth_type='FACE',
    path_mode='COPY',
    embed_textures=True,
    add_leaf_bones=False,
)
bpy.ops.export_scene.gltf(
    filepath=GLB_OUT,
    export_format='GLB',
    use_selection=True,
    export_apply=True,
    export_materials='EXPORT',
    export_image_format='AUTO',
)

report = {
    "status": "SOURCE_DERIVATIVE__RUNTIME_IMPORT_PENDING",
    "source": SOURCE,
    "object": obj.name,
    "source_triangles": source_tris,
    "runtime_triangles": runtime_tris,
    "triangle_ratio": runtime_tris / source_tris if source_tris else 0.0,
    "dimensions_source_units": dimensions,
    "material_slots": [slot.material.name if slot.material else None for slot in obj.material_slots],
    "collision": "NONE__VISUAL_HISM_ONLY",
    "exports": [BLEND_OUT, FBX_OUT, GLB_OUT],
}
with open(REPORT_OUT, "w", encoding="utf-8") as handle:
    json.dump(report, handle, indent=2)
print("LINE_BOSS_PANEL_STILLAGE_DERIVATION " + json.dumps(report))
