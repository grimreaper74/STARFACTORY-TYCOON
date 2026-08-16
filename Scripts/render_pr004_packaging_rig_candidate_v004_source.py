"""Render two independent source-review views of PR-004 PackagingRig v004."""

from pathlib import Path
import math

import bpy
from mathutils import Vector


REPO = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
BLEND = REPO / "SourceAssets/PR004/PackagingRig_v004/LB_PR004_PackagingRig_Candidate_v004.blend"
OUT = REPO / "Saved/ValidationRenders/PR004/PackagingRig_v004"
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BLEND))

# Show the intact delivery state only; runtime tails, ribbon and waste-state
# templates are reviewed separately in their process animations.
for obj in bpy.data.objects:
    if obj.type != "MESH" or not obj.name.startswith("SM_LB_PR004_"):
        continue
    show = (
        "BareCoilCore" in obj.name
        or ("WrapSection_" in obj.name)
        or ("Band_" in obj.name and "CapturedTail" not in obj.name)
        or "EdgeProtector_" in obj.name
        or "IdentityLabel" in obj.name
        or "RFIDTag" in obj.name
    )
    obj.hide_render = not show
    obj.hide_viewport = not show

def simple_material(name, colour, metallic=0.0, roughness=0.7):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*colour, 1.0)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*colour, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return material

floor_material = simple_material("ValidationConcrete", (0.095, 0.105, 0.115), 0.0, 0.84)
bpy.ops.mesh.primitive_plane_add(size=12.0, location=(0.0, 0.0, -1.04))
floor = bpy.context.active_object
floor.name = "ValidationFloor"
floor.data.materials.append(floor_material)

for obj in list(bpy.data.objects):
    if obj.type in {"LIGHT", "CAMERA"}:
        bpy.data.objects.remove(obj, do_unlink=True)

def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()

def area(name, location, energy, size, colour, target=(0.0, 0.0, 0.0)):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = colour
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    look_at(obj, target)

area("Key", (3.8, -4.5, 5.2), 1150.0, 4.0, (1.0, 0.88, 0.73))
area("Fill", (-3.5, -1.6, 2.8), 850.0, 4.5, (0.64, 0.76, 1.0))
area("Rim", (0.5, 4.0, 4.2), 1000.0, 3.5, (0.80, 0.88, 1.0))

camera_data = bpy.data.cameras.new("ValidationCamera")
camera = bpy.data.objects.new("ValidationCamera", camera_data)
bpy.context.collection.objects.link(camera)
bpy.context.scene.camera = camera
camera_data.lens = 58.0

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1400
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.world.color = (0.012, 0.016, 0.022)
scene.view_settings.look = "AgX - Medium High Contrast"

views = {
    "three_quarter": ((3.55, -3.35, 2.55), (0.0, 0.0, 0.0)),
    "face_close": ((3.75, -0.25, 0.80), (0.15, -0.05, 0.0)),
}
for name, (location, target) in views.items():
    camera.location = location
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"pr004_packaging_v004_{name}.png")
    bpy.ops.render.render(write_still=True)
    print(f"LINE_BOSS_PR004_PACKAGING_V004_RENDER {name} {scene.render.filepath}")
