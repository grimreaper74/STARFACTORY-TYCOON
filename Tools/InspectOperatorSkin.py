"""Read-only neutral renderer for external PR005 operator-side Meshy skin."""
import bpy, os
from mathutils import Vector
out = r"C:\\Users\\greg_\\Projects\\LineBossCarFactory_Unreal 5.8\\Saved\\ValidationScreenshots\\MeshyIntake\\0813062913"
os.makedirs(out, exist_ok=True)
s=bpy.context.scene; s.render.engine='BLENDER_EEVEE'; s.render.resolution_x=1600; s.render.resolution_y=1200; s.render.resolution_percentage=100; s.render.image_settings.file_format='PNG'; s.world.color=(.035,.04,.045)
stage=bpy.data.collections.new('TEMP_OPERATOR_INTAKE_STAGE');s.collection.children.link(stage)
def material(name,c):
 m=bpy.data.materials.new(name);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*c,1);b.inputs['Metallic'].default_value=.55;b.inputs['Roughness'].default_value=.32;return m
palette=[(.90,.89,.84),(.03,.04,.045),(.12,.35,.28),(.89,.55,.02),(.36,.40,.42)]
for i,o in enumerate([o for o in s.objects if o.type=='MESH']): o.data.materials.clear();o.data.materials.append(material('TEMP_MAT%02d'%i,palette[i%len(palette)]))
bpy.ops.mesh.primitive_plane_add(size=12,location=(0,0,-.8));floor=bpy.context.object;floor.data.materials.append(material('TEMP_FLOOR',(.20,.22,.22)));[c.objects.unlink(floor) for c in list(floor.users_collection)];stage.objects.link(floor)
def light(n,l,e,z,t):
 d=bpy.data.lights.new(n,'AREA');d.energy=e;d.shape='DISK';d.size=z;o=bpy.data.objects.new(n,d);stage.objects.link(o);o.location=l;o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
light('Key',(-4,5,5),1100,4,(0,0,0));light('Fill',(4,2,4),850,4,(0,0,0));light('Rim',(0,-4,4),950,3,(0,0,0))
d=bpy.data.cameras.new('TEMP_CAMERA');d.lens=52;cam=bpy.data.objects.new('TEMP_CAMERA',d);stage.objects.link(cam);s.camera=cam
def render(name,loc):
 cam.location=loc;cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=os.path.join(out,name);bpy.ops.render.render(write_still=True);print('RENDERED|'+s.render.filepath)
render('01_operator_overview.png',(3.5,-4.5,2.8));render('02_operator_front.png',(0,-5,1.6));render('03_operator_side.png',(4.5,0,1.7));print('INPUT_NOT_SAVED')
