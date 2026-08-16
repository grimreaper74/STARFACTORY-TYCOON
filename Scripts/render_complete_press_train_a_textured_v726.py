"""Blender CLI: fresh material-node/PBR renders of the accepted complete Train A source."""
from pathlib import Path
from datetime import datetime, timezone
import bpy, json, math
from mathutils import Vector
ROOT=Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT=ROOT/r"SourceAssets\Candidate\PressTrains\TrainA\CompleteTrainAAssembly_v660\Review\Textured_v726";OUT.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=1920;scene.render.resolution_y=1080;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.render.image_settings.color_mode='RGBA';scene.view_settings.look='AgX - Medium High Contrast'
world=scene.world or bpy.data.worlds.new('World');scene.world=world;world.use_nodes=True
bg=world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(0.015,0.02,0.024,1);bg.inputs['Strength'].default_value=0.32
for o in list(scene.objects):
 if o.type in {'LIGHT','CAMERA'}:bpy.data.objects.remove(o,do_unlink=True)
def area(name,loc,energy,size,color):
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='RECTANGLE';d.size=size;d.size_y=size*.35;d.color=color
 a=bpy.data.objects.new(name,d);scene.collection.objects.link(a);a.location=Vector(loc);a.rotation_euler=(Vector((0,22.5,3.5))-a.location).to_track_quat('-Z','Y').to_euler();return a
area('KeyWest',(-18,20,26),4200,28,(1.0,.92,.78));area('KeyEast',(18,30,22),3600,26,(.72,.84,1.0));area('LengthFill',(0,5,20),3200,34,(.85,1.0,.88));area('EndFill',(0,48,16),2500,22,(1.0,.80,.62))
def render(name,loc,target,lens):
 d=bpy.data.cameras.new(name);cam=bpy.data.objects.new(name,d);scene.collection.objects.link(cam);scene.camera=cam;d.lens=lens;cam.location=Vector(loc);cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/name);bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
render('TrainA_textured_operator_elevated_v726.png',(-38,-12,24),(0,22.5,3.7),56)
render('TrainA_textured_operator_elevation_v726.png',(-47,22.5,8),(0,22.5,3.6),62)
render('TrainA_textured_service_rear_v726.png',(39,24,15),(0,22.5,3.8),60)
packed=sum(1 for i in bpy.data.images if i.packed_file)
(OUT/'TEXTURED_RENDER_AUDIT_v726.json').write_text(json.dumps({'revision':'v726','generated_utc':datetime.now(timezone.utc).isoformat(),'status':'FRESH_BLENDER_TEXTURED_RENDERS__VISUAL_REVIEW_REQUIRED','source_blend':bpy.data.filepath,'material_count':len(bpy.data.materials),'image_count':len(bpy.data.images),'packed_image_count':packed,'render_engine':'BLENDER_EEVEE','renders':['TrainA_textured_operator_elevated_v726.png','TrainA_textured_operator_elevation_v726.png','TrainA_textured_service_rear_v726.png']},indent=2),encoding='utf-8')
print('LINE_BOSS_TRAIN_A_TEXTURED_RENDER_V726_PASS')
