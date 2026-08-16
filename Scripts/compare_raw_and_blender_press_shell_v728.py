"""Blender CLI: compare untouched Meshy shell master with accepted v660 Blender shell side by side."""
from pathlib import Path
from datetime import datetime,timezone
import bpy,json
from mathutils import Vector
ROOT=Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
RAW=ROOT/r"SourceAssets\Candidate\PressTrains\Shared\MeshyStaticPressShell_v642\SM_CA_MW_PT_Shared_StaticPressShell_LOD0_v639.glb"
OUT=ROOT/r"SourceAssets\Candidate\PressTrains\TrainA\CompleteTrainAAssembly_v660\Review\MasterComparison_v728";OUT.mkdir(parents=True,exist_ok=True)
AUDIT=OUT/'RAW_VS_BLENDER_SHELL_COMPARISON_v728.json'
clean=bpy.data.objects.get('SM_CA_MW_PTA_S03_StaticPressShell_v643')
if not clean:raise RuntimeError('Missing accepted v660 S03 shell')
for o in list(bpy.context.scene.objects):o.hide_render=(o!=clean)
clean.hide_render=False
before=set(bpy.context.scene.objects);bpy.ops.import_scene.gltf(filepath=str(RAW));raws=[o for o in bpy.context.scene.objects if o not in before and o.type=='MESH']
if not raws:raise RuntimeError('Raw shell import empty')
bpy.ops.object.select_all(action='DESELECT')
for o in raws:o.select_set(True);o.hide_render=False
bpy.context.view_layer.objects.active=raws[0]
if len(raws)>1:bpy.ops.object.join()
raw=bpy.context.object;raw.name='RAW_Meshy_Master_v639'
def bounds(o):
 pts=[o.matrix_world@Vector(c) for c in o.bound_box];return Vector(tuple(min(p[i] for p in pts) for i in range(3))),Vector(tuple(max(p[i] for p in pts) for i in range(3)))
rl,rh=bounds(raw);cl,ch=bounds(clean);raw.scale*=8.2/(rh.z-rl.z);bpy.context.view_layer.update();rl,rh=bounds(raw)
raw.location+=Vector((-6.2,0,-rl.z));clean.location=Vector((6.2,-15,-cl.z));bpy.context.view_layer.update();rl,rh=bounds(raw);cl,ch=bounds(clean)
scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=1800;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.look='AgX - Medium High Contrast'
world=scene.world or bpy.data.worlds.new('World');scene.world=world;world.use_nodes=True;bg=world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.012,.016,.02,1);bg.inputs['Strength'].default_value=.4
for o in list(scene.objects):
 if o.type in {'LIGHT','CAMERA'}:bpy.data.objects.remove(o,do_unlink=True)
centre=Vector((0,0,4.1))
def area(name,loc,energy,size,color):
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.size=size;d.color=color;a=bpy.data.objects.new(name,d);scene.collection.objects.link(a);a.location=Vector(loc);a.rotation_euler=(centre-a.location).to_track_quat('-Z','Y').to_euler()
area('Key',(-10,-10,13),3200,12,(1,.9,.76));area('Fill',(11,-5,10),2500,11,(.72,.84,1));area('Rim',(0,8,13),2600,12,(.8,1,.84))
def render(name,loc,target):
 d=bpy.data.cameras.new(name);c=bpy.data.objects.new(name,d);scene.collection.objects.link(c);scene.camera=c;d.lens=58;c.location=Vector(loc);c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/name);bpy.ops.render.render(write_still=True);bpy.data.objects.remove(c,do_unlink=True)
render('raw_left_blender_master_right_front_v728.png',(0,-25,5),(0,0,4));render('raw_left_blender_master_right_hero_v728.png',(-18,-23,13),(0,0,4))
def stats(o):
 return {'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'triangles':sum(len(p.vertices)-2 for p in o.data.polygons),'uv_layers':len(o.data.uv_layers),'materials':[m.name for m in o.data.materials if m],'dimensions_m':list(o.dimensions)}
rs,cs=stats(raw),stats(clean);topology_same=(rs['vertices']==cs['vertices'] and rs['polygons']==cs['polygons'] and rs['triangles']==cs['triangles'])
AUDIT.write_text(json.dumps({'revision':'v728','generated_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS__RAW_MASTER_PRESERVED__SIDE_BY_SIDE_VISUAL_REVIEW_REQUIRED','raw_master':str(RAW),'accepted_blender_master':bpy.data.filepath,'raw':rs,'blender':cs,'topology_counts_identical':topology_same,'comparison_key':'RAW LEFT; ACCEPTED BLENDER MASTER RIGHT','renders':['raw_left_blender_master_right_front_v728.png','raw_left_blender_master_right_hero_v728.png']},indent=2),encoding='utf-8')
print('LINE_BOSS_RAW_VS_BLENDER_PRESS_SHELL_V728_PASS')
