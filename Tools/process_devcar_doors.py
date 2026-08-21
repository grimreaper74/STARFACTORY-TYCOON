"""Process the generated doors: hinge pivots, family dimensions,
palette zones, and mirrored right-side versions."""
import math
import sys

import bpy

sys.path.append(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
import lb_model_kit as kit

BASE = ("C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/"
        "SourceAssets/Candidate/DevCarParts_v001_src/")
DOORS = (("door_front.glb", "Front", 1.03, 0.83),
         ("door_rear.glb", "Rear", 0.92, 0.83))


def load_join(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for ob in meshes:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True,
                                   scale=True)
    return ob


for fname, tag, length, height in DOORS:
    door = load_join(BASE + fname)
    d = door.dimensions
    # Long axis -> X, thin axis -> Y.
    order = sorted(range(3), key=lambda i: -d[i])
    if order[0] == 1:
        door.rotation_euler[2] = math.radians(90.0)
        bpy.ops.object.transform_apply(rotation=True)
    elif order[0] == 2:
        door.rotation_euler[1] = math.radians(90.0)
        bpy.ops.object.transform_apply(rotation=True)
    d = door.dimensions
    if d.y > d.z:
        door.rotation_euler[0] = math.radians(90.0)
        bpy.ops.object.transform_apply(rotation=True)
    scale = length / door.dimensions.x
    door.scale = (scale, scale, scale)
    bpy.ops.object.transform_apply(scale=True)

    mesh = door.data
    # Exterior = the side with more distant faces; make it -Y.
    neg = sum(1 for p in mesh.polygons if p.center.y < 0
              and abs(p.normal.y) > 0.4)
    pos = sum(1 for p in mesh.polygons if p.center.y > 0
              and abs(p.normal.y) > 0.4)
    ys = [v.co.y for v in mesh.vertices]
    mid = (max(ys) + min(ys)) / 2.0
    ext_is_neg = abs(min(ys) - mid) > abs(max(ys) - mid)
    if not ext_is_neg:
        door.rotation_euler[2] = math.radians(180.0)
        bpy.ops.object.transform_apply(rotation=True)

    # Hinge pivot: leading edge, floor of the panel.
    vs = [door.matrix_world @ v.co for v in mesh.vertices]
    door.location = (-min(v.x for v in vs),
                     -(max(v.y for v in vs) + min(v.y for v in vs)) / 2.0,
                     -min(v.z for v in vs))
    bpy.ops.object.transform_apply(location=True)

    kit.MATERIALS.clear()
    kit.glass_material()
    mats = [kit.material(*kit.GREEN), kit.material(*kit.CHARCOAL),
            kit.material(*kit.GLASS)]
    mesh.materials.clear()
    for m in mats:
        mesh.materials.append(m)
    h = door.dimensions.z
    for poly in mesh.polygons:
        if poly.center.z > h * 0.66:
            poly.material_index = 2 if abs(poly.normal.y) > 0.5 else 1
        elif poly.normal.y < -0.25:
            poly.material_index = 0
        else:
            poly.material_index = 1
    if len(mesh.polygons) > 12000:
        dec = door.modifiers.new("Dec", "DECIMATE")
        dec.ratio = 10000 / len(mesh.polygons)
        bpy.context.view_layer.objects.active = door
        bpy.ops.object.modifier_apply(modifier="Dec")

    for side in ("Left", "Right"):
        name = "SM_LB_DevCar_Part_Door{}{}_v001".format(tag, side)
        copy = door.copy()
        copy.data = door.data.copy()
        bpy.context.collection.objects.link(copy)
        if side == "Right":
            copy.scale = (1.0, -1.0, 1.0)
            bpy.context.view_layer.objects.active = copy
            bpy.ops.object.select_all(action="DESELECT")
            copy.select_set(True)
            bpy.ops.object.transform_apply(scale=True)
            import bmesh
            bm = bmesh.new(); bm.from_mesh(copy.data)
            bmesh.ops.reverse_faces(bm, faces=bm.faces)
            bm.to_mesh(copy.data); bm.free()
        for ob in bpy.context.scene.objects:
            ob.select_set(ob is copy)
        # Hide the source door during export by moving it away is not
        # needed: kit.export exports the whole scene, so temporarily
        # unlink the original.
        others = [o for o in bpy.context.scene.objects
                  if o.type == "MESH" and o is not copy]
        for o in others:
            bpy.context.collection.objects.unlink(o)
        copy.name = name
        print("DOOR", name, len(copy.data.polygons))
        kit.export(name, "DevCarParts_v001/" + name)
        kit.preview(name, "DevCarParts_v001/" + name, distance=1.9,
                    height=0.7)
        for o in others:
            bpy.context.collection.objects.link(o)
        bpy.data.objects.remove(copy)
print("DOORS DONE")
