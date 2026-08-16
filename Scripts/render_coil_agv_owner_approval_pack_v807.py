import bpy
import json
import math
import os
from mathutils import Vector

OUT = r"C:\Users\greg_\Projects\LineBoss_Workspace\SourceAssets\Candidate\PressShop\InboundCoilDelivery\UserCoilAGV_v20260809_v807_ApprovalPack"
REVIEW = os.path.join(OUT, "Review")
os.makedirs(REVIEW, exist_ok=True)

# Keep collision/query helpers invisible and leave the v802 master untouched.
for o in bpy.data.objects:
    if o.name.startswith("UCX_"):
        o.hide_render = True
payload = bpy.data.objects.get("AGV_PAYLOAD_WRAPPED_COIL")
if payload is None:
    raise RuntimeError("AGV_PAYLOAD_WRAPPED_COIL missing")

def mat(name, color, metallic=0.0, rough=0.5):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = color
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = color
    p.inputs["Metallic"].default_value = metallic
    p.inputs["Roughness"].default_value = rough
    return m

floor_mat = mat("AGV_APPROVAL_FLOOR", (0.055,0.065,0.075,1), 0.0, 0.7)
bpy.ops.mesh.primitive_plane_add(size=14, location=(0,0,-0.025))
floor = bpy.context.object
floor.name = "APPROVAL_FLOOR_NOT_EXPORT"
floor.data.materials.append(floor_mat)

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1600
scene.render.resolution_y = 1200
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.view_settings.look = "AgX - Medium High Contrast"

world = scene.world
if world is None:
    world = bpy.data.worlds.new("AGV_APPROVAL_WORLD")
    scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.008,0.010,0.014,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.28

for loc, energy, size in [((-5,-6,7),1600,5), ((5,-1,6),1300,4), ((0,6,5),1000,4)]:
    bpy.ops.object.light_add(type="AREA", location=loc)
    l = bpy.context.object
    l.data.energy = energy
    l.data.shape = "DISK"
    l.data.size = size
    l.rotation_euler = (Vector((0,0,0.7))-l.location).to_track_quat("-Z","Y").to_euler()

def camera(loc, target=(0,0,0.65), lens=55, ortho=None):
    bpy.ops.object.camera_add(location=loc)
    c=bpy.context.object
    c.data.lens=lens
    if ortho:
        c.data.type="ORTHO"
        c.data.ortho_scale=ortho
    c.rotation_euler=(Vector(target)-c.location).to_track_quat("-Z","Y").to_euler()
    scene.camera=c
    return c

views = [
    ("01_AGV_Unloaded_Hero_v807.png", False, (4.4,-5.4,3.3), (0,0,0.55), 57, None),
    ("02_AGV_Loaded_Hero_v807.png", True, (4.7,-5.8,3.6), (0,0,0.85), 58, None),
    ("03_AGV_Loaded_LeftSide_v807.png", True, (0,-7.5,1.35), (0,0,0.8), 60, 4.3),
    ("04_AGV_Loaded_Top_v807.png", True, (0,0,8), (0,0,0), 55, 4.3),
    ("05_AGV_Loaded_Front_v807.png", True, (7.5,0,1.35), (0,0,0.8), 60, 3.1),
]
rendered=[]
for fname, loaded, loc, target, lens, ortho in views:
    payload.hide_render = not loaded
    c = camera(loc, target, lens, ortho)
    scene.render.filepath = os.path.join(REVIEW, fname)
    bpy.ops.render.render(write_still=True)
    rendered.append(scene.render.filepath)
    bpy.data.objects.remove(c, do_unlink=True)

payload.hide_render = False
audit = {
    "status":"OWNER_APPROVAL_PACK_READY__V802_MASTER_UNCHANGED__NOT_IMPORTED_TO_UNREAL",
    "source_master":"SourceAssets/Candidate/PressShop/InboundCoilDelivery/UserCoilAGV_v20260809_v802/Cairnwell_Coil_AGV_RuntimeCollisionEnvelope_v802.blend",
    "views":rendered,
    "visual_envelope_m":[2.8,1.7,0.9],
    "payload_envelope_m":[1.65,1.15,1.65],
    "payload_bottom_z_m":0.56,
    "payload_axis":"across vehicle width",
    "route_authority":{"lane_width_m":2.3,"bay_m":[3.4,2.3],"turn_radius_m":1.9378339354},
    "collision_helpers_hidden":True,
    "owner_decision_required":"APPROVE_APPEARANCE_OR_REQUEST_CHANGES_BEFORE_UNREAL_IMPORT",
    "meshy_credits_used":0
}
with open(os.path.join(OUT,"coil_agv_owner_approval_pack_v807.json"),"w",encoding="utf-8") as f:
    json.dump(audit,f,indent=2)
print(json.dumps(audit,indent=2))
