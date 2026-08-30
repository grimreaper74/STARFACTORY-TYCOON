"""Generate the gantry portal from the numbers instead of describing it.

WHY THIS IS GENERATED AND NOT COMMISSIONED
Three separate briefs for this machine produced three plausible wrong
ones - a monorail beam on fixed columns twice, then a portal rotated a
quarter turn with its bridge running ALONG the line. Every brief was
accurate and none was unambiguous, because "gantry crane on a rail"
describes both machines and "straddles the stations" does not say which
axis the bridge crosses.

A portal is defined by numbers the project already holds, so it is built
from them. The span comes straight from GantryRailSpanCm().

THE PIECES ARE SEPARATE BECAUSE THEY MOVE SEPARATELY
  rails    static, laid along the line
  portal   legs + bridge, travels ALONG the rails
  trolley  traverses ACROSS the bridge
  hoist    lowers from the trolley
Modelled as one object the rails would slide down the hall with the
crane, which is exactly how the Meshy drop arrived.
"""
import bpy, sys, os, math
from mathutils import Vector

A = sys.argv[sys.argv.index('--') + 1:]
OUT = A[0]
SPAN_M = float(A[1])          # rail gauge, from GantryRailSpanCm()
RUN_M = float(A[2])           # how far the rails run down the line

# STATED ASSUMPTION, NOT A DERIVED NUMBER. No station declares a height
# anywhere in the codebase, so the bridge underside cannot be computed
# the way the span can. 11 m clears a station arch tall enough to pass a
# 7 m craft envelope with room over it. When station heights become real
# data this should be derived and this comment deleted.
UNDERSIDE_M = 11.0
LEG_M = 1.2                   # leg section, square
BRIDGE_M = 1.8                # bridge beam depth

PALETTE = {
    'graphite_metal':    ((0.068, 0.074, 0.080), 0.25, 0.45),
    'machined_pale':     ((0.672, 0.644, 0.597), 0.05, 0.55),
    'brushed_aluminium': ((0.262, 0.283, 0.305), 0.40, 0.30),
    'livery_accent':     ((0.323, 0.323, 0.315), 0.10, 0.50),
    'dark_rubber':       ((0.017, 0.015, 0.014), 0.00, 0.95),
}

bpy.ops.wm.read_factory_settings(use_empty=True)
mats = {}
for name, (rgb, metal, rough) in PALETTE.items():
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    b.inputs['Metallic'].default_value = metal
    b.inputs['Roughness'].default_value = rough
    mats[name] = m


def box(name, size, at, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=at)
    o = bpy.context.object
    o.name = name
    o.scale = Vector(size)
    bpy.ops.object.transform_apply(location=False, rotation=False,
                                   scale=True)
    o.data.materials.append(mats[mat])
    return o


def tube(name, radius, length, at, axis, mat):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=length,
                                        vertices=16, location=at)
    o = bpy.context.object
    o.name = name
    if axis == 'x':
        o.rotation_euler = (0, math.radians(90), 0)
    elif axis == 'y':
        o.rotation_euler = (math.radians(90), 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=True,
                                   scale=True)
    o.data.materials.append(mats[mat])
    return o


half = SPAN_M / 2.0
groups = {}

# RAILS: two, on the floor, running ALONG the line (the Y axis).
# They are what make the portal legible as a travelling machine. Without
# visible rails a portal reads as a fixed arch, which is the ambiguity
# that let three wrong versions pass review.
rails = []
for sx, tag in ((-half, 'L'), (half, 'R')):
    rails.append(box('rail_bed_' + tag, (0.9, RUN_M, 0.12),
                     (sx, 0, 0.06), 'graphite_metal'))
    rails.append(box('rail_head_' + tag, (0.30, RUN_M, 0.16),
                     (sx, 0, 0.20), 'brushed_aluminium'))
    for i in range(int(RUN_M // 3.0)):
        y = -RUN_M / 2 + 1.5 + i * 3.0
        rails.append(box('rail_sleeper_%s_%02d' % (tag, i),
                         (1.5, 0.45, 0.10), (sx, y, 0.05),
                         'graphite_metal'))
groups['rails'] = rails

# PORTAL: legs outboard of the line, bridge ACROSS it.
portal = []
for sx, tag in ((-half, 'L'), (half, 'R')):
    portal.append(box('leg_' + tag, (LEG_M, LEG_M, UNDERSIDE_M - 0.5),
                      (sx, 0, 0.5 + (UNDERSIDE_M - 0.5) / 2),
                      'graphite_metal'))
    portal.append(box('bogie_' + tag, (1.5, 3.2, 0.55),
                      (sx, 0, 0.50), 'graphite_metal'))
    for k, sy in enumerate((-1.15, 1.15)):
        portal.append(tube('wheel_%s_%d' % (tag, k), 0.32, 0.34,
                           (sx, sy, 0.30), 'x', 'dark_rubber'))
    # A gusset where leg meets bridge, so the corner reads as structure.
    portal.append(box('gusset_' + tag, (LEG_M, 2.4, 1.1),
                      (sx, 0, UNDERSIDE_M - 0.55), 'graphite_metal'))
    portal.append(box('leg_trim_' + tag, (LEG_M + 0.06, 0.35, 0.9),
                      (sx, 0, 3.0), 'livery_accent'))

# The bridge spans the FULL gauge, crossing the line at right angles.
portal.append(box('bridge_beam', (SPAN_M + LEG_M, BRIDGE_M, 1.1),
                  (0, 0, UNDERSIDE_M + 0.55), 'graphite_metal'))
portal.append(box('bridge_deck', (SPAN_M + LEG_M, BRIDGE_M + 0.5, 0.14),
                  (0, 0, UNDERSIDE_M + 1.18), 'machined_pale'))
for k, sy in enumerate((-0.55, 0.55)):
    portal.append(box('traverse_rail_%d' % k, (SPAN_M, 0.16, 0.12),
                      (0, sy, UNDERSIDE_M - 0.06), 'brushed_aluminium'))
portal.append(box('drive_house', (2.6, BRIDGE_M + 0.3, 1.0),
                  (half - 3.0, 0, UNDERSIDE_M + 1.75), 'machined_pale'))
portal.append(box('bridge_trim', (SPAN_M + LEG_M, 0.30, 0.22),
                  (0, BRIDGE_M / 2 + 0.02, UNDERSIDE_M + 0.95),
                  'livery_accent'))
groups['portal'] = portal

# TROLLEY: traverses ACROSS the bridge.
trolley = [box('trolley_frame', (3.0, 2.4, 0.85),
               (0, 0, UNDERSIDE_M - 0.55), 'machined_pale')]
n = 0
for sx in (-1.15, 1.15):
    for sy in (-0.55, 0.55):
        trolley.append(tube('trolley_wheel_%d' % n, 0.20, 0.22,
                            (sx, sy, UNDERSIDE_M - 0.06), 'y',
                            'brushed_aluminium'))
        n += 1
trolley.append(box('trolley_drum', (1.6, 0.7, 0.7),
                   (0, 0, UNDERSIDE_M - 1.15), 'brushed_aluminium'))
groups['trolley'] = trolley

# HOIST: lowers from the trolley; the spreader takes the craft.
hoist = []
DROP = 4.2
n = 0
for sx in (-1.5, 1.5):
    for sy in (-0.5, 0.5):
        hoist.append(tube('hoist_cable_%d' % n, 0.045, DROP,
                          (sx, sy, UNDERSIDE_M - 1.5 - DROP / 2), 'z',
                          'brushed_aluminium'))
        n += 1
SPREAD_Z = UNDERSIDE_M - 1.5 - DROP
hoist.append(box('spreader_beam', (4.6, 0.55, 0.45),
                 (0, 0, SPREAD_Z), 'graphite_metal'))
hoist.append(box('spreader_trim', (4.6, 0.60, 0.10),
                 (0, 0, SPREAD_Z + 0.28), 'livery_accent'))
for k, sx in enumerate((-2.0, 2.0)):
    hoist.append(box('lift_pad_%d' % k, (0.7, 0.7, 0.22),
                     (sx, 0, SPREAD_Z - 0.34), 'dark_rubber'))
    hoist.append(box('lift_arm_%d' % k, (0.28, 0.28, 0.5),
                     (sx, 0, SPREAD_Z - 0.15), 'graphite_metal'))
groups['hoist'] = hoist

os.makedirs(OUT, exist_ok=True)
for gname in ('rails', 'portal', 'trolley', 'hoist'):
    objs = groups[gname]
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.hide_set(False)
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    j = bpy.context.view_layer.objects.active
    j.name = 'LB_Gantry_' + gname
    tris = sum(len(p.vertices) - 2 for p in j.data.polygons)
    mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
    for c in j.bound_box:
        w = j.matrix_world @ Vector(c)
        for i in range(3):
            mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
    bpy.ops.object.select_all(action='DESELECT')
    j.select_set(True)
    bpy.context.view_layer.objects.active = j
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, j.name + '.glb'),
                              export_format='GLB', use_selection=True,
                              export_yup=True, export_apply=True)
    print('EXPORT %-22s %6d tris  %5.1f x %5.1f x %5.1f m'
          % (j.name, tris, (mx - mn).x, (mx - mn).y, (mx - mn).z))
    j.hide_set(True)

print('SPAN %.1f m   UNDERSIDE %.1f m   RUN %.1f m'
      % (SPAN_M, UNDERSIDE_M, RUN_M))
