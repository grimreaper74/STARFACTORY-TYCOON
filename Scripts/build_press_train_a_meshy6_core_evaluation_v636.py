import bpy, math, json, hashlib
from pathlib import Path
from mathutils import Vector

ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = Path(r"C:\Users\greg_\Downloads\Meshy_AI_Cairnwell_S03_Walker_0808080548_texture.glb")
OUT = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/Meshy6CoreEvaluation_v636"
OUT.mkdir(parents=True, exist_ok=True)
STATIONS = {"S02": -15.0, "S03": -7.5, "S04": 0.0, "S05": 7.5, "S06": 15.0}

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def bounds(objects):
    pts = [o.matrix_world @ Vector(c) for o in objects for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi

def look_at(obj, target):
    obj.rotation_euler = ((Vector(target) - obj.location).to_track_quat('-Z', 'Y')).to_euler()

def material(name, colour, metallic=0.0, roughness=0.45):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*colour, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*colour, 1)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    return m

def add_cube(name, location, scale, mat):
    bpy.ops.mesh.primitive_cube_add(location=location)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    return o

def add_text(body, location, size, mat):
    bpy.ops.object.text_add(location=location, rotation=(math.radians(90), 0, 0))
    t = bpy.context.object
    t.data.body = body
    t.data.align_x = 'CENTER'
    t.data.align_y = 'CENTER'
    t.data.size = size
    t.data.extrude = 0.018
    t.data.bevel_depth = 0.006
    t.data.materials.append(mat)
    return t

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.join()
master = bpy.context.object
master.name = 'LB_Meshy6_PressCore_S03'
lo, hi = bounds([master])
master.location -= Vector(((lo.x + hi.x)/2, (lo.y + hi.y)/2, lo.z))
bpy.context.view_layer.update()
lo, hi = bounds([master])
scale = 7.2 / (hi.z - lo.z)
master.scale = (scale, scale, scale)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

collection = bpy.data.collections.new('Train_A_Meshy6_Core')
bpy.context.scene.collection.children.link(collection)
bpy.context.collection.objects.unlink(master)
collection.objects.link(master)
master.location = (STATIONS['S03'], 0, 0)
for station, x in STATIONS.items():
    if station == 'S03':
        obj = master
    else:
        obj = master.copy()
        obj.data = master.data
        collection.objects.link(obj)
        obj.location = (x, 0, 0)
    obj.rotation_euler[2] = math.radians(90)
    obj.name = f'LB_Meshy6_PressCore_{station}'

floor_mat = material('M_SealedConcrete_Bright', (0.28, 0.30, 0.32), 0.0, 0.72)
green = material('M_LabelGreen', (0.025, 0.16, 0.095), 0.15, 0.35)
white = material('M_LabelWhite', (0.92, 0.96, 0.93), 0.0, 0.28)
yellow = material('M_SafetyYellow', (0.95, 0.55, 0.025), 0.1, 0.3)
add_cube('ReviewFloor', (0, 0, -0.14), (23.5, 8.5, 0.14), floor_mat)

for station, x in STATIONS.items():
    add_cube(f'LabelPlate_{station}', (x, -4.65, 7.75), (1.55, 0.08, 0.53), green)
    add_text(station, (x, -4.76, 7.75), 0.72, white)

add_cube('ReviewBanner', (0, -4.65, 9.15), (13.5, 0.08, 0.48), green)
add_text('MESHY 6 CORE PRESS BODIES  |  SUPPORT SYSTEMS PENDING', (0, -4.76, 9.15), 0.48, yellow)

world = bpy.data.worlds.new('BrightReviewWorld')
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.16, 0.18, 0.20, 1)
bg.inputs['Strength'].default_value = 0.48

for name, loc, energy, size in [
    ('Key', (-16, -14, 18), 5200, 9), ('Fill', (16, -8, 15), 4400, 8),
    ('Rim', (8, 14, 18), 5000, 7), ('FrontSoft', (0, -18, 9), 3600, 10)]:
    bpy.ops.object.light_add(type='AREA', location=loc)
    light = bpy.context.object
    light.name = name
    light.data.energy = energy
    light.data.shape = 'DISK'
    light.data.size = size
    look_at(light, (0, 0, 3.5))

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.view_settings.look = 'AgX - Medium High Contrast'

def render(name, loc, target, lens):
    bpy.ops.object.camera_add(location=loc)
    cam = bpy.context.object
    cam.data.lens = lens
    look_at(cam, target)
    scene.camera = cam
    scene.render.filepath = str(OUT / name)
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)

render('TrainA_Meshy6Core_ThreeQuarter_v636.png', (-32, -38, 18), (0, 0, 3.9), 48)
bpy.data.objects['ReviewFloor'].hide_render = True
render('TrainA_Meshy6Core_OperatorElevation_v636.png', (0, -58, 4.8), (0, 0, 4.1), 50)
bpy.data.objects['ReviewFloor'].hide_render = False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'LB_TrainA_Meshy6Core_Evaluation_v636.blend'))

manifest = {
    'revision': 'v636', 'status': 'candidate-review-only',
    'quality_policy': 'Meshy 6 minimum for close/player-visible machinery; Smart Topology excluded',
    'source': str(SOURCE), 'source_sha256': sha256(SOURCE),
    'stations': list(STATIONS), 'support_systems': 'pending Meshy 6 or deliberate Blender construction',
    'old_assets_used': False, 'smart_topology_assets_used': False
}
(OUT / 'MANIFEST_v636.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
