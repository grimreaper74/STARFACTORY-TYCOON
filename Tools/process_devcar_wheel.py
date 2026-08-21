"""Process the generated wheel into the parts kit: hub pivot, Y spin
axis, 0.75 m diameter, palette zones by radius."""
import math
import sys

import bpy

sys.path.append(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
import lb_model_kit as kit

SRC = ("C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/"
       "SourceAssets/Candidate/DevCarParts_v001_src/wheel.glb")
NAME = "SM_LB_DevCar_Part_Wheel_v001"
DIAMETER = 0.75

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
bpy.ops.object.select_all(action="DESELECT")
for ob in meshes:
    ob.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
wheel = bpy.context.view_layer.objects.active
wheel.name = NAME
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# The spin axis is the SHORTEST dimension; rotate it onto Y.
d = wheel.dimensions
axis = min(range(3), key=lambda i: d[i])
if axis == 0:
    wheel.rotation_euler[2] = math.radians(90.0)
elif axis == 2:
    wheel.rotation_euler[0] = math.radians(90.0)
bpy.ops.object.transform_apply(rotation=True)
d = wheel.dimensions
scale = DIAMETER / max(d.x, d.z)
wheel.scale = (scale, scale, scale)
bpy.ops.object.transform_apply(scale=True)
vs = [wheel.matrix_world @ v.co for v in wheel.data.vertices]
cx = (min(v.x for v in vs) + max(v.x for v in vs)) / 2.0
cy = (min(v.y for v in vs) + max(v.y for v in vs)) / 2.0
cz = (min(v.z for v in vs) + max(v.z for v in vs)) / 2.0
wheel.location = (-cx, -cy, -cz)
bpy.ops.object.transform_apply(location=True)
print("WHEEL dims", tuple(round(v, 3) for v in wheel.dimensions),
      "tris", len(wheel.data.polygons))

mesh = wheel.data
kit.glass_material()
mats = [kit.material(*kit.TIRE), kit.material(*kit.CHARCOAL),
        kit.material(*kit.STEEL)]
mesh.materials.clear()
for m in mats:
    mesh.materials.append(m)
R = DIAMETER / 2.0
for poly in mesh.polygons:
    c = poly.center
    r = math.hypot(c.x, c.z)
    if r > R * 0.72:
        poly.material_index = 0        # tire
    elif abs(poly.normal.y) > 0.55:
        poly.material_index = 2        # machined spoke faces
    else:
        poly.material_index = 1        # rim barrel / recesses
if len(mesh.polygons) > 14000:
    dec = wheel.modifiers.new("Dec", "DECIMATE")
    dec.ratio = 12000 / len(mesh.polygons)
    bpy.context.view_layer.objects.active = wheel
    bpy.ops.object.modifier_apply(modifier="Dec")
    print("WHEEL decimated to", len(mesh.polygons))
kit.export(NAME, "DevCarParts_v001/" + NAME)
kit.preview(NAME, "DevCarParts_v001/" + NAME, distance=1.6, height=0.5)
print("WHEEL DONE")
