"""Read-only audit of library candidates.

Usage: blender -b CW_IndustrialDetailLibrary_v001.blend --python AuditIndustrialDetailLibrary.py
Prints dimensions, material-slot count and non-manifold edges. Does not save the blend.
"""
import bpy
import bmesh

prefixes = ("CW_Detail_", "CW_Module_")
objects = sorted(
    (obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj.name.startswith(prefixes)),
    key=lambda obj: obj.name,
)
print("LIBRARY_CANDIDATES|%d" % len(objects))
for obj in objects:
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    non_manifold = sum(1 for edge in bm.edges if not edge.is_manifold)
    bm.free()
    dimensions = tuple(round(value, 5) for value in obj.dimensions)
    slots = len(mesh.materials)
    print(
        "ASSET|%s|dimensions=%s|vertices=%d|faces=%d|material_slots=%d|non_manifold_edges=%d"
        % (obj.name, dimensions, len(mesh.vertices), len(mesh.polygons), slots, non_manifold)
    )
print("INPUT_NOT_SAVED")
