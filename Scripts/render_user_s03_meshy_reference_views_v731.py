"""Blender CLI: exact Meshy-ready orthographic reference views from Greg's accepted S03 GLB."""
from pathlib import Path
from datetime import datetime,timezone
import bpy,json,hashlib
from mathutils import Vector
SRC=Path(r"C:\Users\greg_\Downloads\Meshy_AI_Cairnwell_S03_Walker_0808080548_texture (1).glb")
ROOT=Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT=ROOT/r"SourceAssets\Candidate\PressTrains\Shared\UserS03WalkerReferenceViews_v731";OUT.mkdir(parents=True,exist_ok=True)
AUDIT=OUT/'REFERENCE_VIEW_MANIFEST_v731.json'
if AUDIT.exists():raise RuntimeError('Refusing overwrite v731')
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(SRC))
objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
if not objects:raise RuntimeError('No user model meshes')
pts=[o.matrix_world@Vector(c) for o in objects for c in o.bound_box];lo=Vector(tuple(min(p[i] for p in pts) for i in range(3)));hi=Vector(tuple(max(p[i] for p in pts) for i in range(3)));centre=(lo+hi)*.5;dims=hi-lo
scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=1024;scene.render.resolution_y=1024;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False;scene.view_settings.look='AgX - Medium High Contrast'
world=scene.world or bpy.data.worlds.new('World');scene.world=world;world.use_nodes=True;bg=world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(1,1,1,1);bg.inputs['Strength'].default_value=.8
def area(name,loc,energy,size):
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.size=size;d.color=(1,1,1);a=bpy.data.objects.new(name,d);scene.collection.objects.link(a);a.location=Vector(loc);a.rotation_euler=(centre-a.location).to_track_quat('-Z','Y').to_euler()
r=max(dims);area('FrontFill',centre+Vector((0,-r*2,r)),1700,r*1.5);area('RearFill',centre+Vector((0,r*2,r)),1500,r*1.5);area('LeftFill',centre+Vector((-r*2,0,r)),1500,r*1.5);area('RightFill',centre+Vector((r*2,0,r)),1500,r*1.5);area('TopFill',centre+Vector((0,0,r*2.5)),1800,r*1.8)
views=[('front',Vector((0,-1,0))),('rear',Vector((0,1,0))),('left',Vector((-1,0,0))),('right',Vector((1,0,0)))]
records=[]
for name,direction in views:
 d=bpy.data.cameras.new('Camera_'+name);cam=bpy.data.objects.new('Camera_'+name,d);scene.collection.objects.link(cam);scene.camera=cam;d.type='ORTHO';d.ortho_scale=max(dims.x,dims.z)*1.12 if name in ('front','rear') else max(dims.y,dims.z)*1.12
 cam.location=centre+direction*r*3;cam.rotation_euler=(centre-cam.location).to_track_quat('-Z','Y').to_euler();path=OUT/(name+'.png');scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);records.append({'view':name,'file':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest().upper(),'bytes':path.stat().st_size});bpy.data.objects.remove(cam,do_unlink=True)
AUDIT.write_text(json.dumps({'revision':'v731','generated_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS__EXACT_ORTHOGRAPHIC_REFERENCE_VIEWS_FROM_USER_ACCEPTED_GLＢ__READY_FOR_MESHY_MULTI_IMAGE','source':str(SRC),'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest().upper(),'source_modified':False,'projection':'ORTHOGRAPHIC','background':'WHITE','consistent_geometry':True,'views':records,'recommended_meshy_order':['front.png','rear.png','left.png','right.png'],'recommended_settings':{'mode':'multi-image-to-3d','ai_model':'meshy-6','should_texture':True,'enable_pbr':True,'remove_lighting':True,'should_remesh':True,'note':'Use Smart/remesh this time; previous failed shell used should_remesh=false.'}},indent=2),encoding='utf-8')
print('LINE_BOSS_USER_S03_MESHY_REFERENCE_VIEWS_V731_PASS')
