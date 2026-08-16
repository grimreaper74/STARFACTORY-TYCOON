"""Render an opened source blend without saving or changing it.

Usage: blender -b SOURCE --python RenderSourceSceneAutoFrame.py -- LABEL
The shot frames real source meshes automatically and ignores validation floors.
"""
import bpy, os, sys
from mathutils import Vector

label = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "source"
scene = bpy.context.scene
ignored = ("floor", "ground", "stage", "validation")
meshes = [o for o in scene.objects if o.type == "MESH" and not any(t in o.name.lower() for t in ignored)]
if not meshes:
    raise RuntimeError("No source meshes remain after validation-floor filtering")
verts = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
lo = Vector(tuple(min(getattr(v, axis) for v in verts) for axis in "xyz"))
hi = Vector(tuple(max(getattr(v, axis) for v in verts) for axis in "xyz"))
centre, span = (lo + hi) * .5, hi - lo
radius = max(span.x, span.y, span.z, .5)

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = 1200, 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.world.color = (.022, .025, .027)
for o in scene.objects:
    o.hide_render = o.type == "MESH" and o not in meshes

stage = bpy.data.collections.new("CW_AUTOFRAME_RENDER_STAGE")
scene.collection.children.link(stage)
def material(name, colour, metallic=.4, roughness=.35):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*colour, 1)
    b.inputs["Metallic"].default_value, b.inputs["Roughness"].default_value = metallic, roughness
    return m
bpy.ops.mesh.primitive_plane_add(size=radius * 6, location=(centre.x, centre.y, lo.z - .015))
floor = bpy.context.object
floor.data.materials.append(material("CW_AutoFrameFloor", (.14, .15, .15), 0, .72))
for old in list(floor.users_collection): old.objects.unlink(floor)
stage.objects.link(floor)
def area(name, relative, energy, size):
    data = bpy.data.lights.new(name, "AREA"); data.energy = energy; data.shape = "DISK"; data.size = size
    light = bpy.data.objects.new(name, data); stage.objects.link(light)
    light.location = centre + Vector(relative) * radius
    light.rotation_euler = (centre - light.location).to_track_quat("-Z", "Y").to_euler()
area("CW_AutoFrame_Key", (-1.8, -2.2, 2.8), 1400, radius * 1.6)
area("CW_AutoFrame_Fill", (2.0, -0.5, 1.8), 900, radius * 1.5)
area("CW_AutoFrame_Rim", (0, 2.0, 2.2), 1000, radius * 1.2)
camera_data = bpy.data.cameras.new("CW_AUTOFRAME_CAMERA")
camera = bpy.data.objects.new("CW_AUTOFRAME_CAMERA", camera_data); stage.objects.link(camera)
scene.camera = camera
camera.location = centre + Vector((1.85, -2.35, 1.4)) * radius
camera.rotation_euler = (centre + Vector((0, 0, span.z * .05)) - camera.location).to_track_quat("-Z", "Y").to_euler()
camera.data.lens = 55
out = r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\ValidationScreenshots\IndustrialDetailLibrary_Intake\StandaloneMasters"
os.makedirs(out, exist_ok=True)
scene.render.filepath = os.path.join(out, label + ".png")
bpy.ops.render.render(write_still=True)
print("RENDERED|" + scene.render.filepath)
print("BOUNDS_M|%.5f|%.5f|%.5f" % tuple(span))
print("INPUT_NOT_SAVED")
