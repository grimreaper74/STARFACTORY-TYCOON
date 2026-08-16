"""Blender CLI: inspect and render the raw Meshy v719 unload robot without modifying it."""
from pathlib import Path
import bpy, json, math
from mathutils import Vector
ROOT=Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SRC=ROOT/r"SourceAssets\Candidate\PressTrains\Shared\Meshy6PressUnloadRobot_v719\SM_CA_MW_PressUnloadRobot_Meshy6_Raw_v719.glb"
OUT=ROOT/r"SourceAssets\Candidate\PressTrains\Shared\Meshy6PressUnloadRobot_v719\Review_v725";OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(SRC))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
if not meshes:raise RuntimeError('No Meshy robot meshes')
corners=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box];mn=Vector((min(v.x for v in corners),min(v.y for v in corners),min(v.z for v in corners)));mx=Vector((max(v.x for v in corners),max(v.y for v in corners),max(v.z for v in corners)))
centre=(mn+mx)*0.5;dims=mx-mn
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=meshes[0];bpy.ops.object.shade_smooth_by_angle()
world=bpy.context.scene.world or bpy.data.worlds.new('World');bpy.context.scene.world=world;world.color=(0.025,0.025,0.025)
def area(name,loc,energy,size):
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size;a=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(a);a.location=loc;a.rotation_euler=(math.radians(25),0,math.radians(135));return a
area('Key',centre+Vector((dims.x*1.2,-dims.y*1.4,dims.z*1.5)),1400,max(dims)*1.2);area('Fill',centre+Vector((-dims.x*1.4,dims.y,dims.z)),900,max(dims));area('Rim',centre+Vector((0,dims.y*1.5,dims.z*1.6)),1100,max(dims))
camd=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',camd);bpy.context.collection.objects.link(cam);bpy.context.scene.camera=cam;camd.lens=58
def look(loc):
 cam.location=loc;cam.rotation_euler=(centre-loc).to_track_quat('-Z','Y').to_euler()
def render(name,loc):
 look(loc);bpy.context.scene.render.filepath=str(OUT/name);bpy.ops.render.render(write_still=True)
scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=1280;scene.render.resolution_y=1280;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
r=max(dims)*1.8
render('robot_front_v725.png',centre+Vector((0,-r,dims.z*0.15)));render('robot_side_v725.png',centre+Vector((r,0,dims.z*0.15)));render('robot_hero_v725.png',centre+Vector((r*0.75,-r*0.75,dims.z*0.45)))
tris=sum(len(p.vertices)-2 for o in meshes for p in o.data.polygons)
materials=sorted({m.name for o in meshes for m in o.data.materials if m})
(OUT/'robot_raw_inspection_v725.json').write_text(json.dumps({'revision':'v725','status':'RAW_MESHY_ROBOT_VISUAL_REVIEW_REQUIRED','source':str(SRC),'mesh_object_count':len(meshes),'triangle_count':tris,'bounds_min':list(mn),'bounds_max':list(mx),'dimensions':list(dims),'material_count':len(materials),'materials':materials,'renders':['robot_front_v725.png','robot_side_v725.png','robot_hero_v725.png']},indent=2),encoding='utf-8')
