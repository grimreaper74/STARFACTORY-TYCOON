import bpy, sys, json
from pathlib import Path

args=sys.argv[sys.argv.index("--")+1:]
textured_path, out_dir = Path(args[0]), Path(args[1])
out_dir.mkdir(parents=True, exist_ok=True)

# Split guide is the open file. Retain part1 as the real lifting cradle/deck and
# combine all remaining groups into the fixed chassis.
split=[o for o in bpy.context.scene.objects if o.type=="MESH"]
deck=next(o for o in split if o.name=="model_part1")
chassis_parts=[o for o in split if o!=deck]

# The segmentation export is uniformly 2.0 m long; align it to the 1.901947 m
# textured authority before texture projection.
scale=1.901947021484375/2.0
for o in split:
    o.scale=(scale,scale,scale)
    bpy.context.view_layer.objects.active=o; o.select_set(True)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)

for o in bpy.context.selected_objects: o.select_set(False)
for o in chassis_parts: o.select_set(True)
bpy.context.view_layer.objects.active=chassis_parts[0]
bpy.ops.object.join(); chassis=bpy.context.object; chassis.name="SM_CA_MW_CoilAGV_ChassisSplit_v919"
deck.name="SM_CA_MW_CoilAGV_LiftDeck_v919"

# Conservative reduction before UV generation. Both pieces remain well above
# the silhouette/detail threshold established by the five-view source audit.
for obj,ratio in ((chassis,0.22),(deck,0.28)):
    bpy.context.view_layer.objects.active=obj; obj.select_set(True)
    dec=obj.modifiers.new("LB_RealtimeReduction","DECIMATE"); dec.ratio=ratio; dec.use_collapse_triangulate=True
    bpy.ops.object.modifier_apply(modifier=dec.name)
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=0.9, island_margin=0.006)
    bpy.ops.object.mode_set(mode="OBJECT"); obj.select_set(False)

# Append the untouched textured source as the bake authority.
with bpy.data.libraries.load(str(textured_path), link=False) as (src,dst):
    dst.objects=[n for n in src.objects]
for o in dst.objects:
    if o: bpy.context.collection.objects.link(o)
source=next(o for o in dst.objects if o and o.type=="MESH")

scene=bpy.context.scene; scene.render.engine="CYCLES"
scene.cycles.device="CPU"; scene.cycles.samples=1
scene.render.bake.use_selected_to_active=True
scene.render.bake.use_pass_direct=False; scene.render.bake.use_pass_indirect=False; scene.render.bake.use_pass_color=True
scene.render.bake.cage_extrusion=0.08; scene.render.bake.max_ray_distance=0.16

def bake_piece(obj,size):
    img=bpy.data.images.new(obj.name+"_BaseColor",width=size,height=size,alpha=False)
    mat=bpy.data.materials.new(obj.name+"_MAT"); mat.use_nodes=True
    nodes=mat.node_tree.nodes; bsdf=nodes.get("Principled BSDF")
    tex=nodes.new("ShaderNodeTexImage"); tex.image=img; nodes.active=tex
    mat.node_tree.links.new(tex.outputs["Color"],bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value=0.48; bsdf.inputs["Metallic"].default_value=0.12
    obj.data.materials.clear(); obj.data.materials.append(mat)
    bpy.ops.object.select_all(action="DESELECT"); source.select_set(True); obj.select_set(True); bpy.context.view_layer.objects.active=obj
    bpy.ops.object.bake(type="DIFFUSE")
    img.filepath_raw=str(out_dir/(img.name+".png")); img.file_format="PNG"; img.save()
    return img.filepath_raw

textures={"chassis":bake_piece(chassis,2048),"deck":bake_piece(deck,1024)}
source.hide_render=True; source.hide_viewport=True
bpy.ops.wm.save_as_mainfile(filepath=str(out_dir/"LB_Cairnwell_CoilAGV_TexturedSplit_v919.blend"))
for obj in (chassis,deck):
    bpy.ops.object.select_all(action="DESELECT"); obj.select_set(True); bpy.context.view_layer.objects.active=obj
    bpy.ops.export_scene.gltf(filepath=str(out_dir/(obj.name+".glb")),export_format="GLB",use_selection=True,export_apply=True,export_texcoords=True,export_normals=True,export_materials="EXPORT")
manifest={"status":"TEXTURED_SPLIT_READY_FOR_VISUAL_VALIDATION","source_textured":str(textured_path),"split_source":"Meshy_AI__0809174551_part-segmentation.blend","scale_alignment":scale,"chassis_triangles":len(chassis.data.polygons),"deck_triangles":len(deck.data.polygons),"textures":textures,"meshy_credits_used":0}
(out_dir/"coil_agv_textured_split_v919.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
print("LINE_BOSS_COIL_AGV_SPLIT="+json.dumps(manifest))
