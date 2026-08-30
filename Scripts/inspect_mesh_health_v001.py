"""Check a craft GLB for the defects that matter before it goes into
a game engine: flipped or missing normals, non-manifold edges,
duplicate/loose vertices, degenerate faces, and origins that are not
at the world origin (which throws off in-engine placement).
"""
import bpy, sys, bmesh
from mathutils import Vector

A = sys.argv[sys.argv.index('--') + 1:]
SRC = A[0]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)

meshes = [o for o in bpy.data.objects if o.type == 'MESH']
print('OBJECTS %d' % len(meshes))
for o in meshes:
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.normal_update()

    non_manifold = sum(1 for e in bm.edges if not e.is_manifold)
    degenerate = sum(1 for f in bm.faces if f.calc_area() < 1e-8)
    # Flipped-normal heuristic: faces whose normal points inward
    # relative to the mesh's own centroid.
    centre = Vector((0, 0, 0))
    for v in bm.verts:
        centre += v.co
    if len(bm.verts):
        centre /= len(bm.verts)
    inward = 0
    for f in bm.faces:
        to_face = (f.calc_center_median() - centre)
        if to_face.length > 1e-6 and f.normal.dot(to_face.normalized()) < -0.3:
            inward += 1

    loose_verts = sum(1 for v in bm.verts if not v.link_faces)

    print('%-14s verts=%-6d faces=%-6d nonmanifold_edges=%-5d '
          'degenerate_faces=%-4d loose_verts=%-4d inward_normals~%-4d '
          'origin=(%.2f,%.2f,%.2f)'
          % (o.name, len(bm.verts), len(bm.faces), non_manifold,
             degenerate, loose_verts, inward,
             o.matrix_world.translation.x,
             o.matrix_world.translation.y,
             o.matrix_world.translation.z))
    bm.free()
