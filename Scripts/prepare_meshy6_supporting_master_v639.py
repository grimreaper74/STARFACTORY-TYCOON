"""Create an additive optimized Blender master from one raw Meshy 6 GLB."""
import bpy
import json
import sys
from pathlib import Path
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
source, output_dir, asset_name = Path(argv[0]), Path(argv[1]), argv[2]
target_polygons = int(argv[3])
output_dir.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(source))
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
if not meshes:
    raise RuntimeError("No mesh imported")

bpy.ops.object.select_all(action="DESELECT")
for obj in meshes:
    obj.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
master = bpy.context.object
master.name = asset_name + "_LOD0"
master.data.name = master.name + "_Mesh"

# Floor-seat without changing the generated proportions. Scale remains explicitly
# unverified until assembly against the retained station datum.
corners = [master.matrix_world @ Vector(c) for c in master.bound_box]
min_z = min(c.z for c in corners)
master.location.z -= min_z
bpy.context.view_layer.update()
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

before = len(master.data.polygons)
ratio = min(1.0, target_polygons / max(1, before))
if ratio < 0.999:
    modifier = master.modifiers.new("LB_RuntimeBudget_Decimate", "DECIMATE")
    modifier.decimate_type = "COLLAPSE"
    modifier.ratio = ratio
    modifier.use_collapse_triangulate = True
    bpy.context.view_layer.objects.active = master
    bpy.ops.object.modifier_apply(modifier=modifier.name)

for poly in master.data.polygons:
    poly.use_smooth = True
master["lineboss_source_status"] = "OPTIMIZED_MESHY_SOURCE_NOT_PROMOTED"
master["lineboss_scale_status"] = "TBC_PENDING_RETAINED_DATUM_ASSEMBLY"
master["lineboss_collision_status"] = "NOT_AUTHORED"
master["lineboss_moving_parts_status"] = "PENDING_MEANINGFUL_SEPARATION"

blend_path = output_dir / f"{asset_name}_Master_v639.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
bpy.ops.object.select_all(action="DESELECT")
master.select_set(True)
bpy.context.view_layer.objects.active = master
glb_path = output_dir / f"{asset_name}_LOD0_v639.glb"
bpy.ops.export_scene.gltf(filepath=str(glb_path), export_format="GLB", use_selection=True)

report = {
    "revision": "v639",
    "status": "OPTIMIZED_SOURCE_NOT_PROMOTED",
    "source": str(source),
    "asset": asset_name,
    "polygons_before": before,
    "polygons_after": len(master.data.polygons),
    "target_polygons": target_polygons,
    "scale": "TBC",
    "moving_part_separation": "pending",
    "collision": "pending",
    "blend": str(blend_path),
    "glb": str(glb_path),
}
(output_dir / "optimization_report_v639.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("LB_OPTIMIZED=" + json.dumps(report, separators=(",", ":")))
