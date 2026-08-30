"""Process one drone/dock GLB: join static parts into a body mesh, keep
named moving parts as separate objects, scale to a target real-world
extent, and export a structured GLB ready for Unreal import.

Usage (from Blender, background):
  blender --background --python process_drone_batch_v001.py -- \
      <src.glb> <out.glb> <target_metres_on_long_axis> <moving_prefix1> [moving_prefix2 ...]

A "moving part" is any object whose name starts with one of the given
prefixes (e.g. "rotor_", "wheel_", "leg_"); everything else is joined
into one body mesh named "<stem>_Body". This mirrors the Kit Dolly v002
lesson (join what does not move) while preserving the Scout-era lesson
(named, structured export) for what does.
"""
import bpy, sys, os
from mathutils import Vector, Matrix

A = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT, TARGET_M = A[0], A[1], float(A[2])
MOVING_PREFIXES = tuple(A[3:])

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)

meshes = [o for o in bpy.data.objects if o.type == 'MESH']
if not meshes:
    raise RuntimeError('NO MESH OBJECTS IN %s' % SRC)

# Measure BEFORE any changes, so the scale factor is honest.
mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
for o in meshes:
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c)
        for i in range(3):
            mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
size = mx - mn
long_axis = max(size)
if long_axis <= 0.0:
    raise RuntimeError('DEGENERATE BOUNDS')
scale_factor = TARGET_M / long_axis
print('MEASURED %.3f x %.3f x %.3f  scale_factor=%.4f'
      % (size.x, size.y, size.z, scale_factor))

# BAKE SCALE DIRECTLY INTO MESH DATA - no bpy.ops. Every viewport-family
# operator (transform_apply included) depends on window/region context
# that simply does not exist under --background: it returns {'CANCELLED'}
# with NO exception and NO printed error, so a script that trusts it
# silently ships unscaled geometry. Working on matrix_world / mesh data
# directly sidesteps that class of failure entirely: detach from any
# parent (preserving world transform), fold a uniform world-space scale
# into the object's matrix, then bake that matrix into the vertex data
# and reset the object transform to identity.
ScaleMatrix = Matrix.Scale(scale_factor, 4)
for o in meshes:
    world = o.matrix_world.copy()
    o.parent = None
    o.matrix_world = world
    o.matrix_world = ScaleMatrix @ o.matrix_world
    o.data.transform(o.matrix_world)
    o.matrix_world = Matrix.Identity(4)

# Force a depsgraph refresh before reading bound_box again - it is a
# cached value and does not update immediately after a direct
# mesh.data.transform() call, which produced a misleading stale
# print here on the first run of this script (the FINAL EXTENT print
# further down was correct because the join operator's own internal
# refresh happened to fix the cache by the time it ran; this one is
# not so lucky without an explicit update).
bpy.context.view_layer.update()
mn2 = Vector((1e9,) * 3); mx2 = Vector((-1e9,) * 3)
for o in meshes:
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c)
        for i in range(3):
            mn2[i] = min(mn2[i], w[i]); mx2[i] = max(mx2[i], w[i])
drop = -mn2.z
for o in meshes:
    o.location.z += drop

# Split into moving (kept separate) and static (joined into one body).
moving = [o for o in meshes if o.name.startswith(MOVING_PREFIXES)]
static = [o for o in meshes if o not in moving]
print('MOVING %d parts: %s' % (len(moving), [o.name for o in moving]))
print('STATIC %d parts joined into body' % len(static))

stem = os.path.splitext(os.path.basename(OUT))[0]
if static:
    bpy.ops.object.select_all(action='DESELECT')
    for o in static:
        o.select_set(True)
    bpy.context.view_layer.objects.active = static[0]
    bpy.ops.object.join()
    body = bpy.context.view_layer.objects.active
    body.name = '%s_Body' % stem
else:
    body = None

# Rename moving parts with a stable, engine-facing convention:
# "<stem>_<OriginalMovingName>" (strip Blender's ".001" dedup suffix so
# repeated parts read as a numbered family rather than noise).
seen = {}
for o in moving:
    base = o.name.split('.')[0]
    seen[base] = seen.get(base, 0) + 1
    suffix = '' if seen[base] == 1 else '_%d' % (seen[base] - 1)
    o.name = '%s_%s%s' % (stem, base, suffix)

final_mn = Vector((1e9,) * 3); final_mx = Vector((-1e9,) * 3)
for o in ([body] if body else []) + moving:
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c)
        for i in range(3):
            final_mn[i] = min(final_mn[i], w[i])
            final_mx[i] = max(final_mx[i], w[i])
final_size = final_mx - final_mn
print('FINAL EXTENT %.3f x %.3f x %.3f (target was %.3f on long axis)'
      % (final_size.x, final_size.y, final_size.z, TARGET_M))

bpy.ops.object.select_all(action='DESELECT')
for o in ([body] if body else []) + moving:
    o.select_set(True)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=OUT, use_selection=True,
    export_apply=True)
print('WROTE %s' % OUT)
