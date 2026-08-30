"""Report what a .blend actually contains: meshes, triangles, extents,
materials and image textures. Measurement, not impression - this
project does not accept a direction decision on an unmeasured claim.
"""
import bpy, sys, os
from mathutils import Vector

A = sys.argv[sys.argv.index('--') + 1:]
SRC = A[0]
bpy.ops.wm.open_mainfile(filepath=SRC)

meshes = [o for o in bpy.data.objects if o.type == 'MESH']
print('FILE %s' % os.path.basename(SRC))
print('OBJECTS %d' % len(meshes))
tris = 0
verts = 0
for o in meshes:
    o.data.calc_loop_triangles()
    n = len(o.data.loop_triangles)
    tris += n
    verts += len(o.data.vertices)
    print('  PART %-34s %7d tris  %7d verts  %d mat slots'
          % (o.name, n, len(o.data.vertices), len(o.data.materials)))
print('TOTAL %d tris  %d verts' % (tris, verts))

mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
for o in meshes:
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c)
        for i in range(3):
            mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
s = mx - mn
print('EXTENT %.2f x %.2f x %.2f' % (s.x, s.y, s.z))

print('MATERIALS %d' % len(bpy.data.materials))
for m in bpy.data.materials:
    print('  MAT %s' % m.name)
print('IMAGES %d' % len(bpy.data.images))
for im in bpy.data.images:
    if im.size[0]:
        print('  IMG %-40s %dx%d' % (im.name, im.size[0], im.size[1]))
