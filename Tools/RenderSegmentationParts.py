"""Read-only labelled review-sheet renderer for a split Meshy source.
Usage: blender --background SOURCE --python this.py -- LABEL START END
"""
import bpy, os, sys, math
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:]
label,start,end=args[0],int(args[1]),int(args[2])
out=r"C:\\Users\\greg_\\Projects\\LineBossCarFactory_Unreal 5.8\\Saved\\ValidationScreenshots\\IndustrialDetailLibrary_Intake"
os.makedirs(out,exist_ok=True)
source=[o for o in bpy.context.scene.objects if o.type=='MESH']
source.sort(key=lambda o:o.name)
selected=source[start:end]
s=bpy.context.scene;s.render.engine='BLENDER_EEVEE';s.render.resolution_x=2200;s.render.resolution_y=1600;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.world.color=(.025,.028,.03)
c=bpy.data.collections.new('TEMP_PART_SHEET');s.collection.children.link(c)
def mat(n,col):
 m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*col,1);b.inputs['Metallic'].default_value=.6;b.inputs['Roughness'].default_value=.29;return m
white=mat('TEMP_WARM_WHITE',(.72,.74,.72));green=mat('TEMP_GREEN',(.025,.18,.13));graph=mat('TEMP_GRAPH',(.025,.03,.035));floor_m=mat('TEMP_FLOOR',(.1,.11,.12))
cols=5;rows=max(1,math.ceil(len(selected)/cols));spacing=3.3
for i,src in enumerate(selected):
 # Reconstruct a local, presentation-only copy around each own bounding-box centre.
 o=src.copy();o.data=src.data.copy();c.objects.link(o)
 vs=[o.matrix_world@v.co for v in o.data.vertices];lo=Vector((min(v.x for v in vs),min(v.y for v in vs),min(v.z for v in vs)));hi=Vector((max(v.x for v in vs),max(v.y for v in vs),max(v.z for v in vs)));centre=(lo+hi)/2;size=hi-lo
 for v in o.data.vertices:v.co=src.matrix_world@(v.co) - centre
 o.matrix_world.identity();scale=1.65/max(size);o.scale=(scale,scale,scale)
 o.location=((i%cols-(cols-1)/2)*spacing,(rows-1)/2*spacing-(i//cols)*spacing,.3)
 o.data.materials.clear();o.data.materials.append((white,green,graph)[i%3])
 bpy.ops.mesh.primitive_plane_add(size=2.4,location=(o.location.x,o.location.y,-.55));pl=bpy.context.object;pl.data.materials.append(floor_m);[cc.objects.unlink(pl) for cc in list(pl.users_collection)];c.objects.link(pl)
 fd=bpy.data.curves.new('lbl','FONT');fd.body='%s\n%.2f x %.2f x %.2f'%(src.name.replace('model_part','p'),size.x,size.y,size.z);fd.align_x='CENTER';fd.size=.17;fd.extrude=.003;tx=bpy.data.objects.new('lbl',fd);c.objects.link(tx);tx.location=(o.location.x,o.location.y-1.25,-.48);tx.rotation_euler=(0,0,0);tx.data.materials.append(white)
def light(n,l,e,z):
 d=bpy.data.lights.new(n,'AREA');d.energy=e;d.shape='DISK';d.size=z;o=bpy.data.objects.new(n,d);c.objects.link(o);o.location=l;o.rotation_euler=(Vector((0,0,0))-o.location).to_track_quat('-Z','Y').to_euler()
light('key',(-8,8,12),2500,7);light('fill',(8,5,9),1800,6);light('rim',(0,-8,9),1800,5)
d=bpy.data.cameras.new('TEMP_CAM');d.type='ORTHO';d.ortho_scale=max(cols*spacing,rows*spacing)*1.05;cam=bpy.data.objects.new('TEMP_CAM',d);c.objects.link(cam);s.camera=cam;cam.location=(0,0,16);cam.rotation_euler=(0,0,0)
# Camera points down -Z by default only when zero rotation.
s.render.filepath=os.path.join(out,'%s_%03d_%03d.png'%(label,start,end-1));bpy.ops.render.render(write_still=True);print('RENDERED|'+s.render.filepath);print('INPUT_NOT_SAVED')
