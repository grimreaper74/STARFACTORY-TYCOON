"""Read-only isolated render of a named mesh in the currently opened blend.

Usage: blender -b SOURCE --python RenderNamedMeshDiagnostic.py -- OBJECT LABEL
"""
import bpy, os, sys
from mathutils import Vector

obj_name, label = sys.argv[sys.argv.index("--") + 1:][:2]
obj = bpy.data.objects.get(obj_name)
if not obj or obj.type != "MESH":
    raise RuntimeError("Mesh not found: " + obj_name)
scene = bpy.context.scene
for candidate in scene.objects:
    candidate.hide_render = candidate.type == "MESH" and candidate != obj
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = 1200, 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.world.color = (.025, .028, .03)

def make_material(name, colour):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF")
    principled.inputs["Base Color"].default_value = (*colour, 1)
    principled.inputs["Metallic"].default_value = .55
    principled.inputs["Roughness"].default_value = .29
    return material

stage = bpy.data.collections.new("CW_DIAGNOSTIC_STAGE")
scene.collection.children.link(stage)

# Never move the source object.  The diagnostic copy is baked into a local,
# presentation-only coordinate frame so camera framing is independent of the
# source asset's original world placement.
world_vertices = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
lo = Vector((min(v.x for v in world_vertices), min(v.y for v in world_vertices), min(v.z for v in world_vertices)))
hi = Vector((max(v.x for v in world_vertices), max(v.y for v in world_vertices), max(v.z for v in world_vertices)))
centre = (lo + hi) * .5
diagnostic_mesh = obj.data.copy()
for vertex in diagnostic_mesh.vertices:
    vertex.co = obj.matrix_world @ vertex.co - centre
diagnostic = bpy.data.objects.new("CW_DIAGNOSTIC_COPY", diagnostic_mesh)
stage.objects.link(diagnostic)
diagnostic.matrix_world.identity()
obj.hide_render = True
bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, -.02))
floor = bpy.context.object
floor.data.materials.append(make_material("CW_DiagnosticFloor", (.14, .15, .15)))
for old in list(floor.users_collection):
    old.objects.unlink(floor)
stage.objects.link(floor)

def area(name, location, energy, size):
    data = bpy.data.lights.new(name, "AREA")
    data.energy, data.shape, data.size = energy, "DISK", size
    light = bpy.data.objects.new(name, data)
    stage.objects.link(light)
    light.location = location
    light.rotation_euler = (Vector((0, 0, .75)) - light.location).to_track_quat("-Z", "Y").to_euler()

area("CW_DiagnosticKey", (-4, 4, 5), 1000, 4)
area("CW_DiagnosticFill", (4, 1, 4), 750, 4)
area("CW_DiagnosticRim", (0, -4, 4), 850, 3)
camera_data = bpy.data.cameras.new("CW_DIAGNOSTIC_CAMERA")
camera = bpy.data.objects.new("CW_DIAGNOSTIC_CAMERA", camera_data)
stage.objects.link(camera)
scene.camera = camera
span = max(diagnostic.dimensions)
camera.location = (span * 2.0, -span * 2.5, span * 1.5)
camera.rotation_euler = (Vector((0, 0, span * .45)) - camera.location).to_track_quat("-Z", "Y").to_euler()
out = r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\ValidationScreenshots\IndustrialDetailLibrary_Intake"
os.makedirs(out, exist_ok=True)
scene.render.filepath = os.path.join(out, label + ".png")
bpy.ops.render.render(write_still=True)
print("RENDERED|" + scene.render.filepath)
print("INPUT_NOT_SAVED")
