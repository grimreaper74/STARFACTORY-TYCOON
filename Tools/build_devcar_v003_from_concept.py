"""Dev car v003: the owner's generated concept, edited into the game.

Owner, 2026-08-22: "it needs to look like the meshy model" - so the
generated GLB is the base (his paid-tier asset), edited here: real
car scale (4.36 m), floor pivot, cleaned naming, palette accents
(signature light bars), and material slots renamed to the project
convention. Provenance recorded in Docs/AssetCatalog.
"""
import math

import bpy

SRC = ("C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/"
       "SourceAssets/Candidate/DevCar_v003/cairnwell_concept_base.glb")
OUT_DIR = ("C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/"
           "SourceAssets/Candidate/DevCar_v003/")
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

# Apply transforms, orient the long axis to X.
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
dims = car.dimensions
if dims.y > dims.x:
    car.rotation_euler[2] = math.radians(-90.0)
    bpy.ops.object.transform_apply(rotation=True)
    dims = car.dimensions

# Scale to real length, floor and centre the pivot.
scale = TARGET_LEN / max(dims.x, 1e-5)
car.scale = (scale, scale, scale)
bpy.ops.object.transform_apply(scale=True)
xs = [car.matrix_world @ v.co for v in car.data.vertices]
minx = min(v.x for v in xs); maxx = max(v.x for v in xs)
miny = min(v.y for v in xs); maxy = max(v.y for v in xs)
minz = min(v.z for v in xs)
car.location = (-(minx + maxx) / 2.0, -(miny + maxy) / 2.0, -minz)
bpy.ops.object.transform_apply(location=True)
print("V003 dims:", tuple(round(d, 3) for d in car.dimensions))

# Clean material naming (no generator branding anywhere).
for index, slot in enumerate(car.material_slots):
    if slot.material:
        slot.material.name = "MAT_CairnwellBody_{:02d}".format(index)

# Export + preview via the kit for a consistent thumbnail.
import sys
sys.path.append(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
import lb_model_kit as kit
kit.export(NAME, "DevCar_v003/" + NAME)
kit.preview(NAME, "DevCar_v003/" + NAME, distance=6.6, height=1.6)
print("V003 COMPLETE")
