"""Read-only external Meshy intake visualizer. Never saves the input blend."""
import bpy, os, sys
from mathutils import Vector

out = r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\ValidationScreenshots\MeshyIntake\0813061552"
os.makedirs(out, exist_ok=True)
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1600
scene.render.resolution_y = 1200
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.world.color = (0.035, 0.04, 0.045)

stage = bpy.data.collections.new("TEMP_INTAKE_STAGE")
scene.collection.children.link(stage)

def material(name, color):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value=(*color,1); b.inputs['Metallic'].default_value=.55; b.inputs['Roughness'].default_value=.32
    return m
mats=[material('TEMP_Part_%d'%i, c) for i,c in enumerate([(0.2,.45,.50),(.75,.32,.09),(.25,.28,.32),(.46,.50,.54),(.12,.16,.19),(.60,.62,.60),(.82,.55,.08),(.25,.40,.30),(.62,.27,.12)])]
for i,o in enumerate([o for o in scene.objects if o.type=='MESH']):
    o.data.materials.clear(); o.data.materials.append(mats[i%len(mats)])
    print('PART|%s|verts=%d|polys=%d|dims=%s'%(o.name,len(o.data.vertices),len(o.data.polygons),tuple(round(v,4) for v in o.dimensions)))
bpy.ops.mesh.primitive_plane_add(size=8, location=(0,0,-.12)); floor=bpy.context.object; floor.data.materials.append(material('TEMP_Floor',(.20,.22,.22)))
for c in list(floor.users_collection):c.objects.unlink(floor)
stage.objects.link(floor)
def light(name, loc, energy, size, target):
    d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size
    o=bpy.data.objects.new(name,d);stage.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
light('TEMP_Key',(-4,5,5),1100,4,(0,0,0));light('TEMP_Fill',(4,2,4),850,4,(0,0,0));light('TEMP_Rim',(0,-4,4),950,3,(0,0,0))
d=bpy.data.cameras.new('TEMP_Camera');d.lens=48;cam=bpy.data.objects.new('TEMP_Camera',d);stage.objects.link(cam);scene.camera=cam
def render(filename, loc):
    cam.location=loc;cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=os.path.join(out,filename);bpy.ops.render.render(write_still=True);print('RENDERED|'+scene.render.filepath)
render('01_overview.png',(3.5,-3.8,2.8));render('02_top.png',(0,0,5.5));render('03_side.png',(4,0,1.8))
print('INPUT_NOT_SAVED')
