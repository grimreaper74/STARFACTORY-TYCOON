"""Render a craft GLB from three fixed views so a shape can be judged.

A single screenshot at one angle is not enough to say whether a
silhouette works. This renders side, three-quarter and top on a neutral
ground with even light, at the same scale, so proportions can be
compared rather than guessed at.
"""
import bpy, sys, os, math
from mathutils import Vector

A = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT = A[0], A[1]
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)

meshes = [o for o in bpy.data.objects if o.type == 'MESH']
print('OBJECTS %d' % len(meshes))
tris = 0
for o in meshes:
    o.data.calc_loop_triangles()
    n = len(o.data.loop_triangles)
    tris += n
    print('  PART %-28s %6d tris' % (o.name, n))
print('TOTAL %d tris' % tris)

mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
for o in meshes:
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c)
        for i in range(3):
            mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
ctr = (mn + mx) * 0.5
size = mx - mn
print('EXTENT %.2f x %.2f x %.2f (metres if authored so)'
      % (size.x, size.y, size.z))
span = max(size)

# Flat neutral clay so form reads, not materials.
clay = bpy.data.materials.new('clay')
clay.use_nodes = True
b = clay.node_tree.nodes['Principled BSDF']
b.inputs['Base Color'].default_value = (0.62, 0.61, 0.59, 1.0)
b.inputs['Roughness'].default_value = 0.55
b.inputs['Metallic'].default_value = 0.0
for o in meshes:
    o.data.materials.clear()
    o.data.materials.append(clay)

for nm, energy, rot in (('key', 3.0, (58, 0, 140)),
                        ('fill', 1.1, (66, 0, -40)),
                        ('rim', 1.6, (105, 0, 20))):
    ld = bpy.data.lights.new(nm, 'SUN'); ld.energy = energy
    ld.angle = math.radians(20)
    ob = bpy.data.objects.new(nm, ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.rotation_euler = tuple(math.radians(v) for v in rot)

w = bpy.data.worlds.new('w'); w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (0.42, 0.42, 0.43, 1)
w.node_tree.nodes['Background'].inputs[1].default_value = 0.55
bpy.context.scene.world = w

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 1100, 620
sc.render.image_settings.file_format = 'PNG'
sc.view_settings.view_transform = 'Standard'

tgt = bpy.data.objects.new('t', None); sc.collection.objects.link(tgt)
tgt.location = ctr
cam_d = bpy.data.cameras.new('c'); cam_d.lens = 70
cam = bpy.data.objects.new('c', cam_d); sc.collection.objects.link(cam)
sc.camera = cam
tc = cam.constraints.new('TRACK_TO'); tc.target = tgt
tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'

VIEWS = {'side': (2, -90, 1.55), 'threequarter': (26, -128, 1.75),
         'top': (74, -95, 1.85)}
for name, (elev, azim, dist_k) in VIEWS.items():
    e, a = math.radians(elev), math.radians(azim)
    d = span * dist_k
    cam.location = (ctr.x + d * math.cos(e) * math.cos(a),
                    ctr.y + d * math.cos(e) * math.sin(a),
                    ctr.z + d * math.sin(e))
    bpy.context.view_layer.update()
    sc.render.filepath = os.path.join(OUT, 'scout_%s' % name)
    bpy.ops.render.render(write_still=True)
    print('WROTE', name)
