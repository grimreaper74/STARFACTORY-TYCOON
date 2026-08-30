"""Generate the ship factory hall's SHELL - walls, roof trusses, lights.

WHY THIS EXISTS. The hall had four interior meshes: a door, the gantry,
a column and a stockpile rack. No walls, no roof, no light fittings. So
the factory floor read as a line of machines standing on an infinite
beige plane, which is exactly how a blockout looks. Close-up frames of
the same factory look good - the models are not the problem, the empty
volume around them is.

BUILT, NOT COMMISSIONED, for the same reason the gantry portal was: the
shape is fully determined by numbers the project already holds
(InteriorFloorCm = 18000 x 18000 cm), and a text brief cannot say
"exactly this footprint" without a drawing anyway.

NO ROOF DECK, DELIBERATELY. The camera is a fixed near-isometric
perspective at pitch -35 (ALBSpacecraftPlayerPawn, FOV 48). A solid
ceiling would fill the top of every frame and hide the factory it
covers. Trusses read as "inside a building" from below while the player
still sees the floor between them, which is how factory games with this
camera have always solved it.

NOTHING HUMAN-SCALED. No walkways, handrails, ladders, doors sized for
people or fire exits: nothing on this floor is handled by a person
(owner, standing rule). The wall is a clad industrial shell and the
lights hang from the structure.

Material slots are named for the project's palette so Unreal can bind
real materials by slot - the same names the icon renderer maps.

Usage:
  blender --background --python build_hall_interior_v001.py -- <outdir>
"""
import bpy, sys, os, math

ARGS = sys.argv[sys.argv.index('--') + 1:]
OUT = ARGS[0]
os.makedirs(OUT, exist_ok=True)

PALE = 'machined_pale'
GRAPHITE = 'graphite_metal'
ALU = 'brushed_aluminium'
LAMP = 'lamp_emissive'


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    return m


def box(name, sx, sy, sz, loc, material):
    """A box given by its FULL extents in metres, centred on loc."""
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = (sx, sy, sz)
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat(material))
    return o


def join(objs, name):
    for o in bpy.data.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    j = bpy.context.active_object
    j.name = name
    return j


def export(name):
    """One GLB per mesh. Interchange nests each import in its own
    <Name>/StaticMeshes/ folder and does NOT honour a combine request,
    so a multi-object file arrives as separate assets under a name
    nothing predicts. One file, one mesh, one known path."""
    path = os.path.join(OUT, name + '.glb')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB',
                              export_apply=True)
    print('WROTE', path)


# ---------------------------------------------------------------- wall
# A 6 m bay of clad wall, 12 m tall, built to tile along X. Origin at
# the bay's centre on the floor, so the placer just steps by 6 m.
#
# 12 m of headroom is set by what has to fit under it: the gantry
# portal is 17.0 m tall, so the wall is deliberately SHORTER than the
# crane and the crane's top passes above the wall line. That is honest
# for a hall whose roof is open trusses rather than a sealed box.
def build_wall():
    reset()
    parts = []
    # Cladding, thin, with a recessed channel every 1.5 m read as ribs.
    parts.append(box('clad', 6.0, 0.30, 12.0, (0, 0, 6.0), PALE))
    for i in range(4):
        x = -2.25 + i * 1.5
        parts.append(box('rib_%d' % i, 0.18, 0.42, 11.6, (x, 0, 5.9),
                         ALU))
    # Base kerb - grounds the wall instead of letting it float, and
    # takes the scuffing a floor like this would really get.
    parts.append(box('kerb', 6.0, 0.50, 0.9, (0, 0, 0.45), GRAPHITE))
    # Head beam, the course the trusses land on.
    parts.append(box('head', 6.0, 0.55, 0.7, (0, 0, 12.35), GRAPHITE))
    join(parts, 'SM_LB_IN_WallBay')
    export('SM_LB_IN_WallBay')


# --------------------------------------------------------------- truss
# One 18 m truss bay: two chords, verticals and diagonals. Spans
# between columns; the placer repeats it. Open, so the camera sees the
# floor between the members.
def build_truss():
    reset()
    parts = []
    SPAN, DEPTH = 18.0, 1.6
    parts.append(box('chord_top', SPAN, 0.28, 0.28, (0, 0, DEPTH),
                     GRAPHITE))
    parts.append(box('chord_bot', SPAN, 0.28, 0.28, (0, 0, 0.0),
                     GRAPHITE))
    posts = 7
    for i in range(posts):
        x = -SPAN * 0.5 + i * (SPAN / (posts - 1))
        parts.append(box('post_%d' % i, 0.16, 0.16, DEPTH,
                         (x, 0, DEPTH * 0.5), GRAPHITE))
    # NO DIAGONALS. The first version braced with rotated bars and the
    # imported mesh measured 731 cm deep instead of 160 - the rotation
    # threw the members far outside the intended envelope, which put
    # the truss about 20 m up and clean out of the camera's view. A
    # Vierendeel frame - parallel chords, vertical posts, no diagonals -
    # has a depth that is exactly DEPTH by construction, reads as
    # structure from below just as well, and cannot be wrong.
    join(parts, 'SM_LB_IN_RoofTruss')
    export('SM_LB_IN_RoofTruss')


# --------------------------------------------------------------- light
# A hanging linear fitting. The lamp face is its own material slot so
# Unreal can drive it emissive - "strong clean lighting, blue/white
# indicators" is the settled direction and this is where the light in
# the frame comes from.
def build_light():
    reset()
    parts = []
    parts.append(box('body', 2.4, 0.34, 0.16, (0, 0, 0.08), ALU))
    parts.append(box('lamp', 2.2, 0.26, 0.06, (0, 0, -0.02), LAMP))
    for sx in (-0.9, 0.9):
        parts.append(box('drop_%s' % sx, 0.05, 0.05, 1.2,
                         (sx, 0, 0.68), GRAPHITE))
    join(parts, 'SM_LB_IN_BayLight')
    export('SM_LB_IN_BayLight')


build_wall()
build_truss()
build_light()
print('HALL INTERIOR PIECES DONE')
