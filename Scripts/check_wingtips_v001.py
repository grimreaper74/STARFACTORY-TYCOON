"""Compare the two wingtips directly: for the Hull, find the extreme
point on each side (max +Y and max -Y) and report its full position,
plus the wing's leading and trailing edge X at the tip. A span-only
symmetry check can hide a wing that is the same length but swept or
shaped differently.
"""
import bpy, sys

A = sys.argv[sys.argv.index('--') + 1:]
SRC = A[0]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)

hull = next(o for o in bpy.data.objects if o.name == 'Hull')
verts = [hull.matrix_world @ v.co for v in hull.data.vertices]

right = max(verts, key=lambda v: v.y)
left = min(verts, key=lambda v: v.y)
print('RIGHT TIP  x=%.3f y=%.3f z=%.3f' % (right.x, right.y, right.z))
print('LEFT  TIP  x=%.3f y=%.3f z=%.3f' % (left.x, left.y, left.z))
print('SPAN right=%.3f  left=%.3f  diff=%.4f'
      % (right.y, -left.y, abs(right.y - -left.y)))

# Leading/trailing edge X extent of each wing (points beyond 80% of
# tip span on each side).
thresh = 0.8 * max(right.y, -left.y)
r_pts = [v for v in verts if v.y > thresh]
l_pts = [v for v in verts if v.y < -thresh]
if r_pts:
    print('RIGHT wing outer band: x %.3f..%.3f  (n=%d)'
          % (min(v.x for v in r_pts), max(v.x for v in r_pts), len(r_pts)))
if l_pts:
    print('LEFT  wing outer band: x %.3f..%.3f  (n=%d)'
          % (min(v.x for v in l_pts), max(v.x for v in l_pts), len(l_pts)))
