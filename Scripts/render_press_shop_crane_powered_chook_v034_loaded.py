"""Render the independent v034 FBX carrying the verified packaged coil v005."""

from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
HOOK = ROOT / "SourceAssets/IndustrialKit/BridgeCrane/PoweredCHook/Candidate_v034/SM_LB_Crane_PoweredCHook_Candidate_v034.fbx"
COIL = ROOT / "SourceAssets/IndustrialKit/MasterCoil/Candidate_v005/SM_LB_MasterCoil_Candidate_v005.fbx"
OUT = ROOT / "Saved/ValidationScreenshots/SourceAssets/BridgeCrane/PoweredCHook/Candidate_v034/lb_crane_powered_chook_v034_loaded_verified_coil.png"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(HOOK), use_custom_normals=True)
hook = next(obj for obj in bpy.context.scene.objects if obj.type == "MESH")
before = set(bpy.context.scene.objects)
bpy.ops.import_scene.fbx(filepath=str(COIL), use_custom_normals=True)
coil_objects = [obj for obj in bpy.context.scene.objects if obj not in before]
for obj in coil_objects:
    obj.location = (1.18, 0.0, -0.59)

def material(name, colour, metallic=0.0, roughness=0.5):
    value = bpy.data.materials.new(name)
    value.use_nodes = True
    bsdf = value.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*colour,1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return value

bpy.ops.mesh.primitive_plane_add(size=12.0, location=(0,0,-1.57))
bpy.context.object.data.materials.append(material("Floor",(0.045,0.055,0.065),0.18,0.58))
world = bpy.data.worlds.new("LoadedAuditWorld")
bpy.context.scene.world = world
world.color = (0.012,0.016,0.022)
for location, energy, size in [((-3,-4,5),1700,4.0),((5,-2,3),1300,3.0),((0,4,4),1100,2.5)]:
    bpy.ops.object.light_add(type="AREA", location=location)
    light = bpy.context.object
    light.data.energy = energy
    light.data.shape = "DISK"
    light.data.size = size
    light.rotation_euler = (Vector((0.7,0,-0.25))-light.location).to_track_quat("-Z","Y").to_euler()
bpy.ops.object.camera_add(location=(4.8,-5.5,2.9))
camera = bpy.context.object
camera.rotation_euler = (Vector((0.75,0,-0.15))-camera.location).to_track_quat("-Z","Y").to_euler()
camera.data.lens = 58
scene = bpy.context.scene
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1400
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(OUT)
scene.view_settings.look = "AgX - Medium High Contrast"
bpy.ops.render.render(write_still=True)
print(f"POWERED_CHOOK_V034_LOADED_RENDER_PASS {OUT}")
