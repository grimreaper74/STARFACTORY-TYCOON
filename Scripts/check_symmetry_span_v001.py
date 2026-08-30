"""Check left/right symmetry of a craft GLB across its centreline.

Renders can hide small asymmetries; this measures them. For each mesh,
mirror every vertex across X=0 and find its nearest neighbour in the
original mesh. A perfectly symmetric wing pair reports near-zero
average and max deviation; a genuinely mismatched wing shows up as a
large max deviation localised to one region.
"""
import bpy, sys
from mathutils import Vector
from mathutils.kdtree import KDTree

A = sys.argv[sys.argv.index('--') + 1:]
SRC = A[0]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)

meshes = [o for o in bpy.data.objects if o.type == 'MESH']
for o in meshes:
    verts = [o.matrix_world @ v.co for v in o.data.vertices]
    if len(verts) < 8:
        continue
    kd = KDTree(len(verts))
    for i, v in enumerate(verts):
        kd.insert(v, i)
    kd.balance()

    devs = []
    for v in verts:
        mirrored = Vector((v.x, -v.y, v.z))
        co, idx, dist = kd.find(mirrored)
        devs.append(dist)
    devs.sort()
    n = len(devs)
    avg = sum(devs) / n
    p95 = devs[int(n * 0.95)]
    worst = devs[-1]
    print('%-14s verts=%-6d avg_mirror_dev=%.4f m  p95=%.4f m  max=%.4f m'
          % (o.name, n, avg, p95, worst))
