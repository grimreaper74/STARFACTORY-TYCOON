"""Render a cleanup-derivative review set. Input blend is never overwritten."""
import bpy
import os
import sys
from mathutils import Vector

out_dir = sys.argv[sys.argv.index("--") + 1]
os.makedirs(out_dir, exist_ok=True)
scene = bpy.context.scene
hmi = bpy.data.objects.get("CW_Module_OperatorHMI_CleanDerivative_v002")
if not hmi:
    raise RuntimeError("Clean HMI derivative is missing")
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1600
scene.render.resolution_y = 1200
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.world.color = (0.022, 0.026, 0.03)
def material(name, color, metallic=0.0, roughness=0.5):
    value = bpy.data.materials.new(name); value.use_nodes = True
    node = value.node_tree.nodes.get("Principled BSDF")
    node.inputs["Base Color"].default_value = (*color, 1)
    node.inputs["Metallic"].default_value = metallic
    node.inputs["Roughness"].default_value = roughness
    return value
floor_mat = material("CW_HMIReviewFloor", (0.15, 0.16, 0.17), 0.05, 0.62)
bpy.ops.mesh.primitive_plane_add(size=7, location=(0, 0, 0))
floor = bpy.context.object; floor.data.materials.append(floor_mat)
def lamp(name, location, energy, size):
    data = bpy.data.lights.new(name, "AREA"); data.energy = energy; data.shape = "DISK"; data.size = size
    light = bpy.data.objects.new(name, data); scene.collection.objects.link(light)
    light.location = location
    light.rotation_euler = (Vector((0, 0, 0.65)) - light.location).to_track_quat("-Z", "Y").to_euler()
lamp("CW_HMI_Key", (-3, -4, 4), 950, 3.0)
lamp("CW_HMI_Fill", (3, -1, 3), 650, 3.0)
lamp("CW_HMI_Rim", (0, 4, 4), 850, 2.5)
camera_data = bpy.data.cameras.new("CW_HMI_ReviewCamera")
camera = bpy.data.objects.new("CW_HMI_ReviewCamera", camera_data); scene.collection.objects.link(camera); scene.camera = camera
for filename, position, target in [
    ("01_hmi_clean_three_quarter.png", (2.4, -3.1, 2.0), (0, 0, .72)),
    ("02_hmi_clean_front.png", (0, -3.8, 1.5), (0, 0, .68)),
    ("03_hmi_clean_side.png", (3.7, 0, 1.45), (0, 0, .68))
]:
    camera.location = position
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = os.path.join(out_dir, filename)
    bpy.ops.render.render(write_still=True)
    print("RENDERED|" + scene.render.filepath)
print("INPUT_NOT_SAVED")
