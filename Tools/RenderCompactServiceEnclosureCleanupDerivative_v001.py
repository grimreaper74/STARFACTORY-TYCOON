"""Render the standalone cleaned compact service enclosure review set."""
import bpy
import os
import sys
from mathutils import Vector
out_dir=sys.argv[sys.argv.index("--")+1]; os.makedirs(out_dir,exist_ok=True)
scene=bpy.context.scene; asset=bpy.data.objects.get("CW_Module_CompactServiceEnclosure_CleanDerivative_v001")
if not asset: raise RuntimeError("Clean compact service enclosure missing")
scene.render.engine="BLENDER_EEVEE"; scene.render.resolution_x=1600; scene.render.resolution_y=1200; scene.render.resolution_percentage=100; scene.render.image_settings.file_format="PNG"; scene.world.color=(.022,.026,.03)
def material(name,color):
    value=bpy.data.materials.new(name); value.use_nodes=True; node=value.node_tree.nodes.get("Principled BSDF"); node.inputs["Base Color"].default_value=(*color,1); node.inputs["Roughness"].default_value=.62; return value
bpy.ops.mesh.primitive_plane_add(size=8,location=(0,0,0)); bpy.context.object.data.materials.append(material("CW_ServiceEnclosureReviewFloor",(.15,.16,.17)))
def lamp(name,location,energy,size):
    data=bpy.data.lights.new(name,"AREA"); data.energy=energy; data.shape="DISK"; data.size=size; light=bpy.data.objects.new(name,data); scene.collection.objects.link(light); light.location=location; light.rotation_euler=(Vector((0,0,.95))-light.location).to_track_quat("-Z","Y").to_euler()
lamp("CW_Service_Key",(-4.5,-5,5.5),1300,4);lamp("CW_Service_Fill",(4.5,-1.5,4),900,3.5);lamp("CW_Service_Rim",(0,5,5),1100,3.5)
camera_data=bpy.data.cameras.new("CW_ServiceReviewCamera"); camera=bpy.data.objects.new("CW_ServiceReviewCamera",camera_data); scene.collection.objects.link(camera);scene.camera=camera
for filename,position,target in [("01_service_enclosure_clean_three_quarter.png",(4,-5,3),(0,0,.95)),("02_service_enclosure_clean_front.png",(0,-5.8,1.9),(0,0,.95)),("03_service_enclosure_clean_side.png",(5.6,0,1.9),(0,0,.95))]:
    camera.location=position;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat("-Z","Y").to_euler();scene.render.filepath=os.path.join(out_dir,filename);bpy.ops.render.render(write_still=True);print("RENDERED|"+scene.render.filepath)
print("INPUT_NOT_SAVED")
