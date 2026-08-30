"""Measure the paint booth's actual clear opening - the jamb/header
pieces that define the passage a craft and its gantry must fit
through - separately from the overall shell footprint. The footprint
is an art-direction number; the opening is a hard gameplay constraint.
"""
import bpy, sys
from mathutils import Vector

A = sys.argv[sys.argv.index('--') + 1:]
SRC = A[0]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)

opening_names = ('opening_jamb', 'opening_header', 'opening_seal',
                  'threshold_strip')
pts = []
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    if any(o.name.startswith(n) for n in opening_names):
        for v in o.data.vertices:
            pts.append(o.matrix_world @ v.co)

if not pts:
    print('NO OPENING PARTS FOUND by name - cannot measure the clear passage')
else:
    xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
    print('OPENING BAND extent: x %.2f..%.2f (span %.2f)'
          % (min(xs), max(xs), max(xs) - min(xs)))
    print('OPENING BAND extent: y %.2f..%.2f (span %.2f)'
          % (min(ys), max(ys), max(ys) - min(ys)))
    print('OPENING BAND extent: z %.2f..%.2f (span %.2f)'
          % (min(zs), max(zs), max(zs) - min(zs)))

# Whole-shell extent for reference.
allv = [o.matrix_world @ v.co for o in bpy.data.objects
        if o.type == 'MESH' for v in o.data.vertices]
xs = [p.x for p in allv]; ys = [p.y for p in allv]; zs = [p.z for p in allv]
print('WHOLE SHELL: %.2f x %.2f x %.2f'
      % (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)))
