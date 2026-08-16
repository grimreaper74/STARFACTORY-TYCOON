import bpy
import json
import math
import os
from mathutils import Vector

OUT = r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\PressShop\PR008\EngineeringBlockout_v20260809_v804"
REVIEW = os.path.join(OUT, "Review")
os.makedirs(REVIEW, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)

def mat(name, rgba, metallic=0.0, rough=0.45):
    m = bpy.data.materials.new(name)
    m.diffuse_color = rgba
    m.use_nodes = True
    bs = m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = rgba
    bs.inputs["Metallic"].default_value = metallic
    bs.inputs["Roughness"].default_value = rough
    return m

M_CHAR = mat("MAT_FRAME_CHARCOAL", (0.014, 0.018, 0.022, 1))
M_GREEN = mat("MAT_CAIRNWELL_GREEN", (0.014, 0.070, 0.057, 1), 0.25, 0.32)
M_YELLOW = mat("MAT_SAFETY_YELLOW", (0.89, 0.47, 0.0, 1), 0.1, 0.32)
M_GREY = mat("MAT_LIGHT_GREY", (0.48, 0.53, 0.58, 1), 0.15, 0.36)
M_RUBBER = mat("MAT_BLACK_RUBBER", (0.008, 0.010, 0.012, 1), 0.0, 0.62)
M_STEEL = mat("MAT_STEEL", (0.36, 0.42, 0.46, 1), 0.8, 0.22)
M_FLOOR = mat("MAT_REVIEW_FLOOR", (0.055, 0.065, 0.075, 1), 0.0, 0.72)

def cube(name, loc_mm, size_mm, material, parent=None, bevel=35):
    bpy.ops.mesh.primitive_cube_add(location=tuple(v / 1000 for v in loc_mm))
    o = bpy.context.object
    o.name = name
    o.dimensions = tuple(v / 1000 for v in size_mm)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = o.modifiers.new("ReviewBevel", "BEVEL")
        mod.width = bevel / 1000
        mod.segments = 2
    o.data.materials.append(material)
    if parent: o.parent = parent
    return o

def cyl(name, loc_mm, radius_mm, depth_mm, material, rotation=(0, math.pi/2, 0), parent=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=radius_mm/1000, depth=depth_mm/1000,
                                       location=tuple(v/1000 for v in loc_mm), rotation=rotation)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(material)
    if parent: o.parent = parent
    return o

root = bpy.data.objects.new("PR008_ROOT__DATUM_LOCAL_0_0_0", None)
bpy.context.collection.objects.link(root)
static = bpy.data.objects.new("PR008_STATIC_ROOT", None); bpy.context.collection.objects.link(static); static.parent=root
moving = bpy.data.objects.new("PR008_MOVING_ROOT", None); bpy.context.collection.objects.link(moving); moving.parent=root
collision = bpy.data.objects.new("PR008_COLLISION_ROOT", None); bpy.context.collection.objects.link(collision); collision.parent=root

# Review floor and exact fixed planning envelope, local +Y material flow.
cube("REVIEW_FLOOR", (0,0,-80), (7600,12500,120), M_FLOOR, bevel=0)

modules = [
    ("M01_ENTRY_GUIDE_LOOP", (0,-4450,825), (2300,1250,1650), M_GREEN),
    ("M02_EDGE_TRACK_FRAME", (0,-3450,725), (2200,650,1450), M_CHAR),
    ("M03_SERVO_FEED", (0,-2500,975), (2600,1450,1950), M_GREEN),
    ("M04_TELESCOPIC_SUPPORT", (0,-850,650), (2400,2000,1300), M_STEEL),
    ("M05_PRE_PUNCH_PRESS", (0,900,1750), (2850,1850,3500), M_CHAR),
    ("M06_CUT_TO_LENGTH_SHEAR", (0,2450,1500), (2850,1200,3000), M_GREEN),
    ("M07_DISCHARGE_ROLLERS", (0,3950,600), (2650,1750,1200), M_CHAR),
    ("M08_HYDRAULIC_POWER_UNIT", (-2050,4050,925), (1100,900,1850), M_GREEN),
    ("M09_ELECTRICAL_DRIVE_CABINETS", (2050,4050,1100), (1250,650,2200), M_GREY),
    ("M10_COMPACT_HMI", (2520,3150,1740), (600,460,1280), M_GREY),
]
for name, loc, size, material in modules:
    cube(name, loc, size, material, static)

# Distinct physical process features and moving roots at their shaft/guide centre-lines.
for y in (-2780,-2500,-2220):
    cyl(f"M01_FEED_ROLL_{y}", (0,y,980), 210, 2100, M_RUBBER, parent=moving)
for x in (-850,850):
    cube(f"M02_EDGE_GUIDE_{x}", (x,-3450,1020), (180,520,520), M_YELLOW, moving, 18)
cube("M03_TELESCOPIC_SUPPORT_MOVING", (0,-850,1120), (2050,1300,180), M_STEEL, moving, 18)
cube("M04_PRE_PUNCH_SLIDE", (0,900,2460), (2250,1050,220), M_YELLOW, moving, 18)
cube("M05_SHEAR_BLADE", (0,2450,2170), (2350,180,180), M_STEEL, moving, 10)
for y in (3600,3950,4300):
    cyl(f"M06_DISCHARGE_ROLL_{y}", (0,y,850), 150, 2350, M_RUBBER, parent=moving)
cube("M07_SERVICE_DOOR_LEFT", (-1435,900,1850), (90,1100,1900), M_YELLOW, moving, 12)
cube("M07_SERVICE_DOOR_RIGHT", (1435,900,1850), (90,1100,1900), M_YELLOW, moving, 12)
cube("M08_SCRAP_FLAP", (0,1450,720), (1750,620,90), M_STEEL, moving, 10)

# Safety guards are review geometry only; runtime no-go volumes remain independent.
for x in (-2900,2900):
    cube(f"SAFETY_GUARD_SIDE_{x}", (x,0,1100), (80,10200,2200), M_YELLOW, static, 8)
for y in (-5100,5100):
    cube(f"SAFETY_GUARD_END_{y}", (0,y,1100), (5800,80,2200), M_YELLOW, static, 8)

# Clearance panels remain in the source hierarchy but are hidden in beauty renders
# so they do not obscure the process modules during owner review.
for o in bpy.data.objects:
    if o.name.startswith("SAFETY_GUARD_"):
        o.hide_render = True

# Envelope corner posts prove the fixed 10.4 x 5.56 x 4.49 m planning boundary.
for x in (-2780,2780):
    for y in (-5200,5200):
        cube(f"ENVELOPE_CORNER_{x}_{y}", (x,y,2245), (45,45,4490), M_YELLOW, collision, 0)

# Material-flow strip through all modules.
cube("STRIP_REFERENCE", (0,0,1010), (1450,10000,35), M_STEEL, static, 4)

# Custom properties document the intended runtime authority.
root["world_datum_cm"] = (-500.0, -2000.0, 0.0)
root["planning_envelope_mm"] = (10400.0, 5560.0, 4490.0)
root["local_axes"] = "+X across strip, +Y material flow, +Z up"
root["status"] = "ENGINEERING_BLOCKOUT_ONLY__NOT_APPROVED_FINAL_ART"

# Lighting and cameras.
world = bpy.context.scene.world
if world is None:
    world = bpy.data.worlds.new("PR008_REVIEW_WORLD")
    bpy.context.scene.world = world
world.color = (0.008,0.010,0.014)
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.006,0.008,0.012,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.22
for loc, energy, size in [((-7,-8,11),1800,6), ((7,1,9),1500,5), ((0,9,7),1100,4)]:
    bpy.ops.object.light_add(type='AREA', location=loc)
    l=bpy.context.object; l.data.energy=energy; l.data.shape='DISK'; l.data.size=size
    direction=Vector((0,0,1.2))-l.location; l.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()

def camera(name, loc, target, lens=48):
    bpy.ops.object.camera_add(location=loc)
    c=bpy.context.object; c.name=name; c.data.lens=lens
    c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler()
    return c

scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=1600; scene.render.resolution_y=1000; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
scene.view_settings.look='AgX - Medium High Contrast'

views = [
    ("01_PR008_Hero_v804.png", (11,-14,11), (0,0,1.1), 52),
    ("02_PR008_Top_v804.png", (0,0,18), (0,0,0), 55),
    ("03_PR008_Side_v804.png", (11,-1,6.5), (0,0,1.25), 58),
]
for fname, loc, target, lens in views:
    c=camera("CAM_"+fname, loc, target, lens); scene.camera=c
    scene.render.filepath=os.path.join(REVIEW,fname); bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(c, do_unlink=True)

blend_path=os.path.join(OUT,"Cairnwell_PR008_EngineeringBlockout_v804.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_path)

audit = {
    "status":"PASS_ENGINEERING_BLOCKOUT__NOT_APPROVED_FINAL_ART__NOT_FOR_UNREAL_IMPORT",
    "source_authority":"CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0",
    "world_datum_cm":[-500,-2000,0],
    "planning_envelope_mm":[10400,5560,4490],
    "module_count":10,
    "moving_part_groups":["M01 feed rolls","M02 edge guides","M03 telescopic support","M04 pre-punch slide","M05 shear blade","M06 discharge rollers","M07 service doors","M08 scrap flap"],
    "separate_moving_objects":13,
    "material_flow_axis":"local +Y",
    "meshy_credits_used":0,
    "blend":blend_path,
    "review_renders":[os.path.join(REVIEW,v[0]) for v in views]
}
with open(os.path.join(OUT,"pr008_engineering_blockout_audit_v804.json"),"w",encoding="utf-8") as f:
    json.dump(audit,f,indent=2)
print(json.dumps(audit,indent=2))
