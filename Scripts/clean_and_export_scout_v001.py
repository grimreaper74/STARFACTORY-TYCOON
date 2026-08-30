"""Weld duplicate vertices and recalculate normals on each of the six
Scout assemblies, then re-export as a clean GLB.

WHY THIS IS NEEDED. Inspection found every object's non-manifold edge
count exactly equal to its vertex count - no vertex is shared between
adjacent triangles, so the mesh arrived as a disconnected triangle
soup rather than a welded surface. That is not visible in a render
(each triangle still carries the right position and normal) but it
roughly TRIPLES the vertex count Nanite has to build a cluster
hierarchy from, and it is worth cleaning before this becomes the
game's hero asset.

Weld tolerance is small (0.1 mm) so it only merges truly coincident
vertices - it must not round off intentional hard edges into rounded
ones.
"""
import bpy, sys, bmesh

A = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT = A[0], A[1]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)

meshes = [o for o in bpy.data.objects if o.type == 'MESH']
for o in meshes:
    bpy.context.view_layer.objects.active = o
    for other in bpy.data.objects:
        other.select_set(False)
    o.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    # Merge by distance welds coincident verts left unwelded by export;
    # 0.1 mm is well below any intentional gap on a 12 m craft.
    bpy.ops.mesh.remove_doubles(threshold=0.0001)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    before = len(o.data.vertices)
    o.data.calc_loop_triangles()
    print('%-14s verts=%-6d faces=%-6d' % (
        o.name, before, len(o.data.loop_triangles)))

for o in meshes:
    o.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB',
                          use_selection=True, export_apply=True)
print('WROTE', OUT)
