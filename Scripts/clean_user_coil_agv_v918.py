import bpy, json, sys
from pathlib import Path

args = sys.argv[sys.argv.index("--") + 1:]
out = Path(args[0])
out.mkdir(parents=True, exist_ok=True)

meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
if len(meshes) != 1:
    raise RuntimeError(f"Expected one textured master mesh, found {len(meshes)}")
obj = meshes[0]
obj.name = "SM_CA_MW_CoilAGV_Chassis_v918"

# Conservative reduction: retains the textured master silhouette and UVs while
# removing enough Meshy density for a practical real-time Nanite source.
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
before = len(obj.data.polygons)
dec = obj.modifiers.new("LB_ConservativeRealtimeReduction", "DECIMATE")
dec.decimate_type = "COLLAPSE"
dec.ratio = 0.22
dec.use_collapse_triangulate = True
bpy.ops.object.modifier_apply(modifier=dec.name)

for poly in obj.data.polygons:
    poly.use_smooth = True
obj.data.set_sharp_from_angle(angle=0.785398)

bpy.ops.wm.save_as_mainfile(filepath=str(out / "LB_Cairnwell_CoilAGV_CleanMaster_v918.blend"))
bpy.ops.export_scene.gltf(
    filepath=str(out / "SM_CA_MW_CoilAGV_Chassis_v918.glb"),
    export_format="GLB", use_selection=True, export_apply=True,
    export_texcoords=True, export_normals=True, export_materials="EXPORT",
)

payload = {
    "source": bpy.data.filepath,
    "object": obj.name,
    "triangles_before": before,
    "triangles_after": len(obj.data.polygons),
    "dimensions_m": list(obj.dimensions),
    "material_slots": len(obj.material_slots),
    "uv_layers": len(obj.data.uv_layers),
    "status": "CLEANED_TEXTURED_MASTER_READY_FOR_UNREAL_VALIDATION",
    "meshy_credits_used": 0,
}
(out / "coil_agv_clean_v918.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
print("LINE_BOSS_COIL_AGV_CLEAN=" + json.dumps(payload))
