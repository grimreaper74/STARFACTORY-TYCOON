"""Project the earlier packed S03 PBR UVs onto the aligned 105-part split geometry."""
import bpy
import json
from pathlib import Path
from mathutils import Vector

root = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
master_path = root / "SourceAssets/Candidate/PressTrains/S03_FormRestrike/SplitMotion_v964/Cairnwell_S03_Front_O_EarlierTexturedMaster_v964.glb"
blend_output = root / "SourceAssets/Candidate/PressTrains/S03_FormRestrike/SplitMotion_v964/Cairnwell_S03_Front_O_TexturedSplit_v966.blend"
glb_output = root / "SourceAssets/Candidate/PressTrains/S03_FormRestrike/SplitMotion_v964/Cairnwell_S03_Front_O_TexturedSplit_v966.glb"
audit_output = root / "Saved/Audits/PressShopGeometry/s03_textured_split_uv_transfer_v966.json"
split_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj.name.startswith("model_part")]
if len(split_objects) != 105:
    raise RuntimeError(f"expected 105 split parts, found {len(split_objects)}")

def bounds(objects):
    points = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    return low, high

split_low, split_high = bounds(split_objects)
before = set(bpy.context.scene.objects)
bpy.ops.import_scene.gltf(filepath=str(master_path))
imported = [obj for obj in bpy.context.scene.objects if obj not in before and obj.type == "MESH"]
if len(imported) != 1:
    raise RuntimeError(f"expected one textured master, found {len(imported)}")
master = imported[0]
master.name = "S03_TEXTURE_TRANSFER_MASTER_v966"
master_low, master_high = bounds([master])
split_size = split_high - split_low
master_size = master_high - master_low
ratios = [split_size[i] / master_size[i] for i in range(3)]
scale = sum(ratios) / 3.0
master.scale *= scale
bpy.context.view_layer.objects.active = master
master.select_set(True)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
master_low, master_high = bounds([master])
master.location += (split_low + split_high) * 0.5 - (master_low + master_high) * 0.5
bpy.context.view_layer.update()
material = master.data.materials[0] if master.data.materials else None
if material is None or len(master.data.uv_layers) == 0:
    raise RuntimeError("textured master lacks material or UV data")

# Give each original part a temporary material identity, join once, and perform
# one nearest-surface search instead of 105 two-million-polygon searches.
bpy.ops.object.select_all(action="DESELECT")
for index, obj in enumerate(split_objects):
    marker = bpy.data.materials.new(f"S03_PART_MARKER_{index:03d}")
    obj.data.materials.clear()
    obj.data.materials.append(marker)
    for polygon in obj.data.polygons:
        polygon.material_index = 0
    obj.select_set(True)
bpy.context.view_layer.objects.active = split_objects[0]
bpy.ops.object.join()
joined = bpy.context.view_layer.objects.active
joined.name = "S03_JOINED_FOR_UV_TRANSFER_v966"
if len(joined.data.uv_layers) == 0:
    joined.data.uv_layers.new(name="UVMap")
modifier = joined.modifiers.new(name="S03_UV_TRANSFER_v966", type="DATA_TRANSFER")
modifier.object = master
modifier.use_loop_data = True
modifier.data_types_loops = {"UV"}
modifier.loop_mapping = "POLYINTERP_NEAREST"
bpy.ops.object.modifier_apply(modifier=modifier.name)

# Restore the 105 logical parts using their temporary material identities.
bpy.context.view_layer.objects.active = joined
joined.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.separate(type="MATERIAL")
bpy.ops.object.mode_set(mode="OBJECT")
split_objects = [obj for obj in bpy.context.selected_objects if obj.type == "MESH" and obj != master]
if len(split_objects) != 105:
    raise RuntimeError(f"separation restored {len(split_objects)} parts, expected 105")
split_objects.sort(key=lambda obj: obj.data.materials[0].name if obj.data.materials else obj.name)
for index, obj in enumerate(split_objects):
    obj.name = f"S03_SPLIT_PART_{index:03d}_v966"
    obj.data.materials.clear()
    obj.data.materials.append(material)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
bpy.data.objects.remove(master, do_unlink=True)
for image in bpy.data.images:
    if image.name != "Render Result" and image.source == "FILE" and not image.packed_file:
        image.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(blend_output))
bpy.ops.object.select_all(action="DESELECT")
for obj in split_objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active = split_objects[0]
bpy.ops.export_scene.gltf(
    filepath=str(glb_output),
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_materials="EXPORT",
)
payload = {
    "revision": "v966",
    "status": "PASS__PACKED_PBR_UV_TRANSFER_TO_105_SPLIT_PARTS",
    "split_source": str(root / "SourceAssets/Candidate/PressTrains/S03_FormRestrike/SplitMotion_v964/Cairnwell_S03_Front_O_SplitMotion_v964.blend"),
    "textured_master": str(master_path),
    "uniform_alignment_scale": scale,
    "axis_ratios": ratios,
    "part_count": len(split_objects),
    "all_parts_have_uv": all(len(obj.data.uv_layers) > 0 for obj in split_objects),
    "blend_output": str(blend_output),
    "glb_output": str(glb_output),
    "meshy_credits_used_by_codex": 0,
}
audit_output.parent.mkdir(parents=True, exist_ok=True)
audit_output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print("LINE_BOSS_S03_TEXTURED_SPLIT_V966_PASS", scale, len(split_objects))
