import bpy, bmesh, sys, json
from pathlib import Path
from mathutils.kdtree import KDTree

args=sys.argv[sys.argv.index("--")+1:]
split_path,out=Path(args[0]),Path(args[1]); out.mkdir(parents=True,exist_ok=True)
source=next(o for o in bpy.context.scene.objects if o.type=="MESH")
source.name="SM_CA_MW_CoilAGV_Chassis_v920"

# Load only the segmented V-cradle/deck as a spatial selection guide.
with bpy.data.libraries.load(str(split_path),link=False) as (src,dst):
    dst.objects=["model_part1"]
guide=dst.objects[0]; bpy.context.collection.objects.link(guide)
guide.scale=(1.901947021484375/2.0,)*3
bpy.context.view_layer.objects.active=guide; guide.select_set(True)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); guide.select_set(False)

kd=KDTree(len(guide.data.vertices))
for i,v in enumerate(guide.data.vertices): kd.insert(guide.matrix_world@v.co,i)
kd.balance()

# Meshy segmentation follows the original surface closely. Select source faces
# when at least two vertices lie within 18 mm of the approved deck guide.
mesh=source.data
near=[False]*len(mesh.vertices)
for i,v in enumerate(mesh.vertices):
    _,_,dist=kd.find(source.matrix_world@v.co); near[i]=dist<=0.018
selected=0
for v in mesh.vertices: v.select=False
for e in mesh.edges: e.select=False
for p in mesh.polygons:
    p.select=sum(1 for vi in p.vertices if near[vi])>=2
    selected+=int(p.select)
mesh.update()
if selected<50000: raise RuntimeError(f"Deck extraction implausibly small: {selected} faces")

bpy.context.view_layer.objects.active=source; source.select_set(True)
bpy.ops.object.mode_set(mode="OBJECT")
bpy.context.tool_settings.mesh_select_mode=(False,False,True)
before_objects=set(bpy.data.objects)
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.separate(type="SELECTED"); bpy.ops.object.mode_set(mode="OBJECT")
new_meshes=[o for o in bpy.data.objects if o not in before_objects and o.type=="MESH"]
if len(new_meshes)!=1: raise RuntimeError(f"Expected one separated deck, found {len(new_meshes)}")
deck=new_meshes[0]; chassis=source
deck.name="SM_CA_MW_CoilAGV_LiftDeck_v920"; chassis.name="SM_CA_MW_CoilAGV_Chassis_v920"
bpy.data.objects.remove(guide,do_unlink=True)

for obj,ratio in ((chassis,0.25),(deck,0.32)):
    bpy.context.view_layer.objects.active=obj; bpy.ops.object.select_all(action="DESELECT"); obj.select_set(True)
    dec=obj.modifiers.new("LB_UVPreservingRealtimeReduction","DECIMATE"); dec.ratio=ratio; dec.use_collapse_triangulate=True
    bpy.ops.object.modifier_apply(modifier=dec.name)

bpy.ops.wm.save_as_mainfile(filepath=str(out/"LB_Cairnwell_CoilAGV_OriginalTextureSplit_v920.blend"))
for obj in (chassis,deck):
    bpy.ops.object.select_all(action="DESELECT"); obj.select_set(True); bpy.context.view_layer.objects.active=obj
    bpy.ops.export_scene.gltf(filepath=str(out/(obj.name+".glb")),export_format="GLB",use_selection=True,export_apply=True,export_texcoords=True,export_normals=True,export_materials="EXPORT")
manifest={"status":"ORIGINAL_TEXTURE_UV_SPLIT_READY_FOR_VISUAL_VALIDATION","selection_faces":selected,"chassis_triangles":len(chassis.data.polygons),"deck_triangles":len(deck.data.polygons),"dimensions_m":list(chassis.dimensions),"meshy_credits_used":0}
(out/"coil_agv_original_texture_split_v920.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
print("LINE_BOSS_COIL_AGV_V920="+json.dumps(manifest))
