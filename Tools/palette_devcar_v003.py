"""Palette pass for dev car v003 - per-face geometric assignment on the
concept mesh: emerald body, dark glass in the recessed DLO, black
tires with steel alloys, light blades front and rear."""
import math
import sys

import bpy

sys.path.append(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
import lb_model_kit as kit

SRC = ("C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/"
       "SourceAssets/Candidate/DevCar_v003/cairnwell_concept_base.glb")
NAME = "SM_LB_DevCar_Concept_v003"
TARGET_LEN = 4.36

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
bpy.ops.object.select_all(action="DESELECT")
for ob in meshes:
    ob.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
car = bpy.context.view_layer.objects.active
car.name = NAME
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
if car.dimensions.y > car.dimensions.x:
    car.rotation_euler[2] = math.radians(-90.0)
    bpy.ops.object.transform_apply(rotation=True)
scale = TARGET_LEN / max(car.dimensions.x, 1e-5)
car.scale = (scale, scale, scale)
bpy.ops.object.transform_apply(scale=True)
vs = [car.matrix_world @ v.co for v in car.data.vertices]
minx = min(v.x for v in vs); maxx = max(v.x for v in vs)
miny = min(v.y for v in vs); maxy = max(v.y for v in vs)
minz = min(v.z for v in vs)
car.location = (-(minx + maxx) / 2.0, -(miny + maxy) / 2.0, -minz)
bpy.ops.object.transform_apply(location=True)

mesh = car.data
L, W, H = car.dimensions
print("V3 dims", round(L, 2), round(W, 2), round(H, 2))

kit.glass_material()
mats = [kit.material(*kit.GREEN), kit.material(*kit.GLASS),
        kit.material(*kit.TIRE), kit.material(*kit.STEEL),
        kit.material(*kit.CHARCOAL), kit.material(*kit.WARMWHITE),
        kit.material(*kit.RED)]
mesh.materials.clear()
for m in mats:
    mesh.materials.append(m)
BODY, GLASS, TIRE, STEEL, CHAR, WHITE, RED = range(7)

# Wheel centres estimated from the silhouette: axles at ~20% and ~82%.
ax_f = -L / 2.0 + 0.20 * L
ax_r = -L / 2.0 + 0.82 * L
wheel_r = 0.33 * H

for poly in mesh.polygons:
    c = poly.center
    n = poly.normal
    idx = BODY
    in_wheel = False
    for ax in (ax_f, ax_r):
        if (abs(c.x - ax) < wheel_r * 1.05 and abs(c.y) > W * 0.36
                and c.z < wheel_r * 1.9 and n.z < 0.55):
            in_wheel = True
            wheel_ax = ax
            break
    if in_wheel:
        idx = (STEEL if abs(c.y) > W * 0.44 and abs(n.y) > 0.6
               and abs(c.x - wheel_ax) < wheel_r * 0.8
               and c.z < wheel_r * 1.4 else TIRE)
    elif (c.z > H * 0.64 and abs(n.y) > 0.60
          and -L * 0.18 < c.x < L * 0.38):
        idx = GLASS                       # side DLO
    elif (c.z > H * 0.68 and n.x < -0.45
          and -L * 0.30 < c.x < -L * 0.02):
        idx = GLASS                       # windscreen
    elif c.z > H * 0.70 and n.x > 0.40 and c.x > L * 0.30:
        idx = GLASS                       # rear screen
    elif c.x < -L / 2.0 + 0.05 and 0.34 * H < c.z < 0.50 * H:
        idx = WHITE                       # front light blade
    elif (c.x > L / 2.0 - 0.035 and 0.62 * H < c.z < 0.70 * H
          and abs(c.y) < W * 0.42):
        idx = RED                         # rear light blade
    elif c.z < H * 0.13:
        idx = CHAR                        # aprons and splitter line
    poly.material_index = idx

kit.export(NAME, "DevCar_v003/" + NAME)
kit.preview(NAME, "DevCar_v003/" + NAME, distance=6.6, height=1.6)
print("PALETTE DONE")
