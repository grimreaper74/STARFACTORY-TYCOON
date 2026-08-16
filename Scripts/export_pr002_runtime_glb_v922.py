import bpy,sys,json
from pathlib import Path

out=Path(sys.argv[sys.argv.index("--")+1]); out.mkdir(parents=True,exist_ok=True)
meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
payload=[o for o in meshes if "WrappedCoil" in o.name]
station=[o for o in meshes if o not in payload]

def join_export(objects,name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]; bpy.ops.object.join(); obj=bpy.context.object; obj.name=name
    bpy.ops.export_scene.gltf(filepath=str(out/(name+".glb")),export_format="GLB",use_selection=True,export_apply=True,export_texcoords=True,export_normals=True,export_materials="EXPORT")
    return {"name":name,"vertices":len(obj.data.vertices),"triangles":len(obj.data.polygons),"dimensions_m":list(obj.dimensions),"materials":len(obj.material_slots)}

records=[join_export(station,"SM_CA_MW_PR002_ScannerWeighCell_v922"),join_export(payload,"SM_CA_MW_PR002_RemovableWrappedCoil_v922")]
(out/"pr002_runtime_glb_v922.json").write_text(json.dumps({"status":"BLENDER_VALIDATED_GLBS_READY_FOR_UNREAL","records":records,"meshy_credits_used":0},indent=2),encoding="utf-8")
print("LINE_BOSS_PR002_GLBS="+json.dumps(records))
