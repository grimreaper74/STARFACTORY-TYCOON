"""Split a single-object mesh into its loose parts and report them.

Meshy returns one object called mesh_node even when the model is
plainly a ship laid out with its components. Blender can separate that
by loose parts; whether the result is USABLE depends on how many
pieces come out and how big they are, so this reports rather than
assumes.
"""
import bpy, sys, os
from mathutils import Vector

A = sys.argv[sys.argv.index('--') + 1:]
SRC = A[0]
OUT = A[1] if len(A) > 1 else ''

bpy.ops.wm.open_mainfile(filepath=SRC)
for o in list(bpy.data.objects):
    if o.type in {'CAMERA', 'LIGHT'}:
        bpy.data.objects.remove(o, do_unlink=True)

meshes = [o for o in bpy.data.objects if o.type == 'MESH']
print('BEFORE %d object(s)' % len(meshes))

for o in bpy.data.objects:
    o.select_set(False)
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.separate(type='LOOSE')
bpy.ops.object.mode_set(mode='OBJECT')

parts = [o for o in bpy.data.objects if o.type == 'MESH']
print('AFTER %d loose part(s)' % len(parts))

rows = []
for o in parts:
    o.data.calc_loop_triangles()
    n = len(o.data.loop_triangles)
    mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c)
        for i in range(3):
            mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
    s = mx - mn
    ctr = (mn + mx) * 0.5
    rows.append((n, o.name, s, ctr))

rows.sort(key=lambda r: -r[0])
print('%-22s %8s  %-22s %s' % ('part', 'tris', 'size', 'centre'))
for n, name, s, c in rows[:24]:
    print('%-22s %8d  %5.2f x %5.2f x %5.2f   (%5.2f, %5.2f, %5.2f)'
          % (name[:22], n, s.x, s.y, s.z, c.x, c.y, c.z))
tiny = sum(1 for r in rows if r[0] < 50)
print('PARTS %d   under-50-tri fragments %d' % (len(rows), tiny))
if OUT:
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'split.blend'))
    print('SAVED split.blend')
