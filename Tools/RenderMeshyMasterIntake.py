"""Read-only neutral renderer for a Meshy master passed after --."""
import bpy,os,sys
from mathutils import Vector
label=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'master'
out=r"C:\\Users\\greg_\\Projects\\LineBossCarFactory_Unreal 5.8\\Saved\\ValidationScreenshots\\MeshyIntake\\Masters"
os.makedirs(out,exist_ok=True);s=bpy.context.scene;s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1200;s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.world.color=(.035,.04,.045)
c=bpy.data.collections.new('TEMP_MASTER_STAGE');s.collection.children.link(c)
def m(n,col):
 x=bpy.data.materials.new(n);x.use_nodes=True;b=x.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*col,1);b.inputs['Metallic'].default_value=.48;b.inputs['Roughness'].default_value=.32;return x
for o in [o for o in s.objects if o.type=='MESH']:o.data.materials.clear();o.data.materials.append(m('TEMP_MASTER',(.72,.74,.73)))
bpy.ops.mesh.primitive_plane_add(size=12,location=(0,0,-1));floor=bpy.context.object;floor.data.materials.append(m('TEMP_FLOOR',(.18,.2,.2)));[q.objects.unlink(floor) for q in list(floor.users_collection)];c.objects.link(floor)
def lamp(n,l,e,z):
 d=bpy.data.lights.new(n,'AREA');d.energy=e;d.shape='DISK';d.size=z;o=bpy.data.objects.new(n,d);c.objects.link(o);o.location=l;o.rotation_euler=(Vector((0,0,0))-o.location).to_track_quat('-Z','Y').to_euler()
lamp('Key',(-4,5,5),1100,4);lamp('Fill',(4,2,4),850,4);lamp('Rim',(0,-4,4),950,3)
d=bpy.data.cameras.new('TEMP_CAM');d.lens=52;cam=bpy.data.objects.new('TEMP_CAM',d);c.objects.link(cam);s.camera=cam;cam.location=(3.5,-4.5,2.8);cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=os.path.join(out,label+'.png');bpy.ops.render.render(write_still=True);print('RENDERED|'+s.render.filepath);print('INPUT_NOT_SAVED')
