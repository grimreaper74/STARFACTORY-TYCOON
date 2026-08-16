"""Render a material-only Cairnwell module review set."""
import bpy
import os
import sys
from mathutils import Vector
out_dir, module_kind=sys.argv[sys.argv.index("--")+1:][:2];os.makedirs(out_dir,exist_ok=True)
object_name={"hmi":"CW_Module_OperatorHMI_CairnwellLivery_v001","cabinet":"CW_Module_ElectricalCabinet_CairnwellLivery_v001"}[module_kind]
asset=bpy.data.objects.get(object_name)
if not asset: raise RuntimeError("Livery asset missing: "+object_name)
scene=bpy.context.scene;scene.render.engine="BLENDER_EEVEE";scene.render.resolution_x=1600;scene.render.resolution_y=1200;scene.render.resolution_percentage=100;scene.render.image_settings.file_format="PNG";scene.world.color=(.022,.026,.03)
def material(name,color):
    value=bpy.data.materials.new(name);value.use_nodes=True;node=value.node_tree.nodes.get("Principled BSDF");node.inputs["Base Color"].default_value=(*color,1);node.inputs["Roughness"].default_value=.62;return value
bpy.ops.mesh.primitive_plane_add(size=7,location=(0,0,0));bpy.context.object.data.materials.append(material("CW_LiveryReviewFloor",(.15,.16,.17)))
def lamp(name,location,energy,size,target):
    data=bpy.data.lights.new(name,"AREA");data.energy=energy;data.shape="DISK";data.size=size;light=bpy.data.objects.new(name,data);scene.collection.objects.link(light);light.location=location;light.rotation_euler=(Vector(target)-light.location).to_track_quat("-Z","Y").to_euler()
height={"hmi":.65,"cabinet":1.0}[module_kind]
lamp("CW_LiveryKey",(-4,-4,5),1200,3.5,(0,0,height));lamp("CW_LiveryFill",(4,-1,3.5),800,3.0,(0,0,height));lamp("CW_LiveryRim",(0,4,4.5),1000,3.0,(0,0,height))
data=bpy.data.cameras.new("CW_LiveryReviewCamera");data.type="ORTHO";camera=bpy.data.objects.new("CW_LiveryReviewCamera",data);scene.collection.objects.link(camera);scene.camera=camera
points=[asset.matrix_world@Vector(corner) for corner in asset.bound_box];low=Vector((min(point.x for point in points),min(point.y for point in points),min(point.z for point in points)));high=Vector((max(point.x for point in points),max(point.y for point in points),max(point.z for point in points)));centre=(low+high)*.5;span=max((high-low).x,(high-low).y,(high-low).z);data.ortho_scale=span*1.45
angles={"hmi":[("01_hmi_cairnwell_three_quarter.png",Vector((1.0,-1.25,.72))),("02_hmi_cairnwell_front.png",Vector((0,-1.6,.25)))],"cabinet":[("01_cabinet_cairnwell_three_quarter.png",Vector((1.12,-1.32,.72))),("02_cabinet_cairnwell_front.png",Vector((0,-1.65,.18)))]}[module_kind]
for filename,direction in angles:
    camera.location=centre+direction.normalized()*span*3.0;camera.rotation_euler=(centre-camera.location).to_track_quat("-Z","Y").to_euler();scene.render.filepath=os.path.join(out_dir,filename);bpy.ops.render.render(write_still=True);print("RENDERED|"+scene.render.filepath)
print("INPUT_NOT_SAVED")
