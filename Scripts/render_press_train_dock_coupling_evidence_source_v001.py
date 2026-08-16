"""Render neutral source evidence for DockCouplingEvidence_v001."""

import bpy
import math
from pathlib import Path
from mathutils import Vector


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = ROOT / "SourceAssets/PressTrains/Shared/DockCouplingEvidence_v001"
bpy.ops.wm.open_mainfile(filepath=str(SOURCE / "CA_MW_PressTrain_DockCouplingEvidence_v001.blend"))
scene = bpy.context.scene

world = bpy.data.worlds.new("DockEvidenceNeutralWorld") if not scene.world else scene.world
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.018, 0.022, 0.024, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.22

bpy.ops.mesh.primitive_plane_add(size=16, location=(0, 0, -0.52))
floor = bpy.context.object
floor.name = "RenderFloor_NotSource"
mat = bpy.data.materials.new("RenderFloorMaterial")
mat.diffuse_color = (0.055, 0.065, 0.068, 1)
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = mat.diffuse_color
bsdf.inputs["Roughness"].default_value = 0.68
floor.data.materials.append(mat)

# Neutral context proxies show how the stage-local evidence spans the retained
# cart edge and fixed dock. They exist only in this render process and are not
# saved into the reusable source asset.
proxy_mat = bpy.data.materials.new("ContextProxyMaterial")
proxy_mat.diffuse_color = (0.026, 0.035, 0.038, 1)
proxy_mat.use_nodes = True
proxy_bsdf = proxy_mat.node_tree.nodes.get("Principled BSDF")
proxy_bsdf.inputs["Base Color"].default_value = proxy_mat.diffuse_color
proxy_bsdf.inputs["Metallic"].default_value = 0.38
proxy_bsdf.inputs["Roughness"].default_value = 0.62

def proxy_box(name, dims, loc):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(proxy_mat)

proxy_box("RetainedCartEdge_ContextOnly", (0.52, 4.35, 0.92), (-1.94, 0.0, 0.38))
proxy_box("FixedDock_ContextOnly", (0.52, 4.35, 1.34), (-3.12, 0.0, 0.58))

def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()

for name, location, energy, size in (
    ("Key", (2.8, -4.5, 5.2), 1250, 4.0),
    ("Fill", (-5.5, -2.0, 3.2), 850, 3.5),
    ("Rim", (-3.5, 4.0, 4.8), 1050, 3.0),
):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = location
    aim(obj, (-2.45, 0.0, 0.55))

cam_data = bpy.data.cameras.new("SourceEvidenceCamera")
camera = bpy.data.objects.new("SourceEvidenceCamera", cam_data)
scene.collection.objects.link(camera)
scene.camera = camera
camera.location = (4.8, -6.8, 3.8)
aim(camera, (-2.48, 0.0, 0.55))
cam_data.lens = 58

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.render.filepath = str(SOURCE / "Validation" / "dock_coupling_engaged_source_v001.png")
Path(scene.render.filepath).parent.mkdir(parents=True, exist_ok=True)
scene.render.image_settings.color_mode = "RGBA"
scene.view_settings.look = "AgX - Medium High Contrast"
bpy.ops.render.render(write_still=True)
print(scene.render.filepath)
