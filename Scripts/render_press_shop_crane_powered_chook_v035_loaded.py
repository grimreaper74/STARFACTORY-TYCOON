"""Render v035 with the verified packaged master coil in side and bore-axis views."""

from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
HOOK=ROOT/"SourceAssets/IndustrialKit/BridgeCrane/PoweredCHook/Candidate_v035/SM_LB_Crane_PoweredCHook_Candidate_v035.fbx"
COIL=ROOT/"SourceAssets/IndustrialKit/MasterCoil/Candidate_v005/SM_LB_MasterCoil_Candidate_v005.fbx"
OUT=ROOT/"Saved/ValidationScreenshots/SourceAssets/BridgeCrane/PoweredCHook/Candidate_v035"
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(HOOK),use_custom_normals=True)
before=set(bpy.context.scene.objects)
bpy.ops.import_scene.fbx(filepath=str(COIL),use_custom_normals=True)
for obj in [value for value in bpy.context.scene.objects if value not in before]: obj.location=(1.50,0,-0.59)

def mat(name,c,m=0.0,r=0.5):
    value=bpy.data.materials.new(name); value.use_nodes=True; bsdf=value.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value=(*c,1); bsdf.inputs["Metallic"].default_value=m; bsdf.inputs["Roughness"].default_value=r; return value
bpy.ops.mesh.primitive_plane_add(size=12,location=(0,0,-1.57)); bpy.context.object.data.materials.append(mat("Floor",(0.04,0.05,0.06),0.2,0.62))
world=bpy.data.worlds.new("LoadedWorld"); bpy.context.scene.world=world; world.color=(0.01,0.014,0.02)
for loc,energy,size in [((-3,-4,5),1700,4),((5,-2,3),1300,3),((0,4,4),1100,2.5)]:
    bpy.ops.object.light_add(type="AREA",location=loc); light=bpy.context.object; light.data.energy=energy; light.data.shape="DISK"; light.data.size=size
    light.rotation_euler=(Vector((0.75,0,-0.2))-light.location).to_track_quat("-Z","Y").to_euler()
scene=bpy.context.scene; scene.render.engine="BLENDER_EEVEE"; scene.render.resolution_x=1500; scene.render.resolution_y=1050; scene.render.resolution_percentage=100; scene.render.image_settings.file_format="PNG"; scene.view_settings.look="AgX - Medium High Contrast"
def render(name,loc,target,lens):
    bpy.ops.object.camera_add(location=loc); camera=bpy.context.object; camera.rotation_euler=(Vector(target)-camera.location).to_track_quat("-Z","Y").to_euler(); camera.data.lens=lens; scene.camera=camera
    path=OUT/f"lb_crane_powered_chook_v035_loaded_{name}.png"; scene.render.filepath=str(path); bpy.ops.render.render(write_still=True); bpy.data.objects.remove(camera,do_unlink=True); return path
paths=[render("side",(4.8,-5.6,2.8),(0.78,0,-0.18),58),render("bore_axis",(4.9,-0.32,0.25),(1.18,0,-0.59),62)]
print("\n".join(str(path) for path in paths))
