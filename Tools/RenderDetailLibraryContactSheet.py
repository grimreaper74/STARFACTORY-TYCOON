"""Render a contact sheet from the standalone detail-library blend."""
import bpy,os,math
from mathutils import Vector
OUT=r"C:\\Users\\greg_\\Projects\\LineBossCarFactory_Unreal 5.8\\SourceAssets\\Shared\\CairnwellIndustrialDetailLibrary_v001\\ValidationRenders"
scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=2400;scene.render.resolution_y=1800;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.world.color=(.025,.028,.03)
lib=bpy.data.collections['CW_IndustrialDetailLibrary_v001'];objs=sorted([o for o in lib.objects if o.type=='MESH'],key=lambda o:o.name);stage=bpy.data.collections.new('CONTACT_SHEET_STAGE');scene.collection.children.link(stage)
for obj in scene.objects:
 obj.hide_render=True
def mat(n,c):
 m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*c,1);b.inputs['Metallic'].default_value=.5;b.inputs['Roughness'].default_value=.3;return m
white=mat('SHEET_WHITE',(.75,.76,.74));floor=mat('SHEET_FLOOR',(.12,.13,.14))
cols=4;rows=math.ceil(len(objs)/cols);spacing=3.3
for i,src in enumerate(objs):
 o=src.copy();o.data=src.data.copy();stage.objects.link(o);o.hide_render=False;vs=[v.co for v in o.data.vertices];lo=Vector((min(v.x for v in vs),min(v.y for v in vs),min(v.z for v in vs)));hi=Vector((max(v.x for v in vs),max(v.y for v in vs),max(v.z for v in vs)));centre=(lo+hi)/2
 for v in o.data.vertices:v.co-=centre
 scale=1.32/max(hi-lo);o.scale=(scale,scale,scale);o.location=((i%cols-(cols-1)/2)*spacing,(rows-1)/2*spacing-(i//cols)*spacing,.25)
 bpy.ops.mesh.primitive_plane_add(size=2.45,location=(o.location.x,o.location.y,-.52));p=bpy.context.object;p.data.materials.append(floor);[c.objects.unlink(p) for c in list(p.users_collection)];stage.objects.link(p);p.hide_render=False
 d=bpy.data.curves.new('label','FONT');d.body=src.name.replace('CW_Detail_','').replace('_',' ');d.align_x='CENTER';d.size=.16;d.extrude=.002;t=bpy.data.objects.new('label',d);stage.objects.link(t);t.location=(o.location.x,o.location.y-1.22,-.48);t.data.materials.append(white);t.hide_render=False
def lamp(n,l,e,z):
 d=bpy.data.lights.new(n,'AREA');d.energy=e;d.shape='DISK';d.size=z;o=bpy.data.objects.new(n,d);stage.objects.link(o);o.hide_render=False;o.location=l;o.rotation_euler=(Vector((0,0,0))-o.location).to_track_quat('-Z','Y').to_euler()
lamp('key',(-8,8,14),2800,8);lamp('fill',(8,4,10),2000,7);lamp('rim',(0,-8,10),2000,5)
# Include the label and tile margins above and below the outer rows.  This is
# a review image only; source library geometry is never moved or saved here.
d=bpy.data.cameras.new('CONTACT_SHEET_CAMERA');d.type='ORTHO';d.ortho_scale=max(cols*spacing,rows*spacing+2.1)*1.16;cam=bpy.data.objects.new('CONTACT_SHEET_CAMERA',d);stage.objects.link(cam);cam.hide_render=False;scene.camera=cam;cam.location=(0,0,16);cam.rotation_euler=(0,0,0);scene.render.filepath=os.path.join(OUT,'CW_IndustrialDetailLibrary_v001_ContactSheet.png');bpy.ops.render.render(write_still=True);print('CONTACT_SHEET|'+scene.render.filepath)
