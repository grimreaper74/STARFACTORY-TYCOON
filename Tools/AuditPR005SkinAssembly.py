"""Read-only object/bounds audit of a PR005 visual-skin review derivative.

Usage: blender -b PR005_CairnwellMeshySkin_v010.blend --python AuditPR005SkinAssembly.py
Does not save the input file.
"""
import bpy
from mathutils import Vector

for obj in sorted(bpy.context.scene.objects, key=lambda value: value.name):
    if obj.type != "MESH":
        continue
    vertices = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    if not vertices:
        continue
    lo = Vector((min(v.x for v in vertices), min(v.y for v in vertices), min(v.z for v in vertices)))
    hi = Vector((max(v.x for v in vertices), max(v.y for v in vertices), max(v.z for v in vertices)))
    collections = ",".join(collection.name for collection in obj.users_collection)
    print(
        "OBJECT|%s|collections=%s|dims=%s|lo=%s|hi=%s|hidden=%s|role=%s"
        % (
            obj.name,
            collections,
            tuple(round(value, 3) for value in obj.dimensions),
            tuple(round(value, 3) for value in lo),
            tuple(round(value, 3) for value in hi),
            obj.hide_render,
            obj.get("Role", ""),
        )
    )
print("INPUT_NOT_SAVED")
