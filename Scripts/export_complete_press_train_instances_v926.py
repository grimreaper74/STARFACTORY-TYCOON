"""Realise the approved v005 Blender collection instances and export one intact train."""
import bpy
from pathlib import Path

out_dir = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\PressTrains\TrainA\CompleteApprovedRuntime_v20260810_v926")
out_dir.mkdir(parents=True, exist_ok=True)

# The source master is assembled with linked collection instances. Copy the renderable
# members of each instance explicitly, multiplying by the instance world matrix. Blender's
# bulk duplicates_make_real operator discards these offsets in background mode.
instances = [o for o in bpy.context.scene.objects if o.type == "EMPTY" and o.instance_collection]
if len(instances) != 14:
    raise RuntimeError(f"Expected 14 approved collection instances, found {len(instances)}")

runtime_collection = bpy.data.collections.new("CA_MW_CompleteApprovedPressTrain_Runtime_v926")
bpy.context.scene.collection.children.link(runtime_collection)
realised = []
for instance in instances:
    for source in instance.instance_collection.all_objects:
        if source.type not in {"MESH", "CURVE"}:
            continue
        clone = source.copy()
        clone.data = source.data.copy()
        clone.name = f"{instance.name}__{source.name}"
        runtime_collection.objects.link(clone)
        clone.parent = None
        clone.matrix_world = instance.matrix_world @ source.matrix_world
        realised.append(clone)
if not realised:
    raise RuntimeError("No objects realised from the approved train")

# Remove every review-only object and retain only the realised production geometry.
keep = set(realised)
for obj in list(bpy.data.objects):
    if obj not in keep:
        bpy.data.objects.remove(obj, do_unlink=True)

# Ensure linked data is local and preserve source materials/textures.
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.make_local(type="ALL")

blend_out = out_dir / "Cairnwell_PressTrain_CompleteApproved_Runtime_v926.blend"
glb_out = out_dir / "Cairnwell_PressTrain_CompleteApproved_Runtime_v926.glb"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_out), copy=True)
bpy.ops.export_scene.gltf(
    filepath=str(glb_out),
    export_format="GLB",
    use_selection=False,
    export_apply=True,
    export_materials="EXPORT",
    export_texcoords=True,
    export_normals=True,
    export_tangents=True,
    export_cameras=False,
    export_lights=False,
)
print("LINE_BOSS_COMPLETE_APPROVED_TRAIN_EXPORT_V926", len(realised), blend_out, glb_out)
