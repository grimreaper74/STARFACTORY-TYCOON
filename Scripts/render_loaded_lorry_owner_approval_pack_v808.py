import bpy
import json
import os
from mathutils import Vector

OUT = r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\PressShop\InboundCoilDelivery\LorryLoadedWrappedCoils_v20260809_v808_ApprovalPack"
REVIEW = os.path.join(OUT, "Review")
os.makedirs(REVIEW, exist_ok=True)

# Remove only transient studio objects in memory; the v004 master is never saved.
for o in list(bpy.data.objects):
    if o.type in {"LIGHT", "CAMERA"}:
        bpy.data.objects.remove(o, do_unlink=True)

def mat(name, color, metallic=0.0, rough=0.55):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color=color
    m.use_nodes=True
    p=m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value=color
    p.inputs["Metallic"].default_value=metallic
    p.inputs["Roughness"].default_value=rough
    return m

bpy.ops.mesh.primitive_plane_add(size=30, location=(0,0,-0.025))
floor=bpy.context.object
floor.name="LORRY_APPROVAL_FLOOR_NOT_EXPORT"
floor.data.materials.append(mat("LORRY_APPROVAL_FLOOR",(0.055,0.065,0.075,1),0,0.72))

scene=bpy.context.scene
scene.render.engine="BLENDER_EEVEE"
scene.render.resolution_x=1800
scene.render.resolution_y=1100
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.view_settings.look="AgX - Medium High Contrast"
world=scene.world
if world is None:
    world=bpy.data.worlds.new("LORRY_APPROVAL_WORLD")
    scene.world=world
world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Color"].default_value=(0.008,0.010,0.014,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value=0.25

for loc, energy, size in [((-9,-10,12),2400,8), ((8,-2,10),1900,7), ((0,10,9),1500,7)]:
    bpy.ops.object.light_add(type="AREA", location=loc)
    l=bpy.context.object; l.data.energy=energy; l.data.shape="DISK"; l.data.size=size
    l.rotation_euler=(Vector((0,0,1.5))-l.location).to_track_quat("-Z","Y").to_euler()

def cam(loc,target=(0,0,1.6),lens=55,ortho=None):
    bpy.ops.object.camera_add(location=loc)
    c=bpy.context.object
    c.data.lens=lens
    if ortho:
        c.data.type="ORTHO"; c.data.ortho_scale=ortho
    c.rotation_euler=(Vector(target)-c.location).to_track_quat("-Z","Y").to_euler()
    scene.camera=c
    return c

views=[
    ("01_Lorry_Loaded_Hero_v808.png",(18,-16,10),(0,0,1.65),58,None),
    ("02_Lorry_Loaded_LeftSide_v808.png",(0,-24,2.6),(0,0,1.7),60,18.2),
    ("03_Lorry_Loaded_Rear_v808.png",(24,0,2.4),(3.3,0,1.55),60,5.8),
    ("04_Lorry_Loaded_Top_v808.png",(0,0,30),(0,0,0),55,18.2),
    ("05_Trailer_Coils_Stands_Close_v808.png",(14,-10,6),(3.0,0,1.45),62,None),
]
rendered=[]
for fname,loc,target,lens,ortho in views:
    c=cam(loc,target,lens,ortho)
    scene.render.filepath=os.path.join(REVIEW,fname)
    bpy.ops.render.render(write_still=True)
    rendered.append(scene.render.filepath)
    bpy.data.objects.remove(c,do_unlink=True)

audit={
    "status":"OWNER_APPROVAL_PACK_READY__V004_MASTER_UNCHANGED__NO_UNREAL_MAP_CHANGE",
    "source_master":"SourceAssets/Candidate/PressShop/InboundCoilDelivery/LorryLoadedWrappedCoils_v20260809_v004/Cairnwell_Lorry_Loaded_WrappedCoils_ApprovedStands_v004.blend",
    "views":rendered,
    "assembly_bounds_m":[16.5,2.55,4.0],
    "coil_count":4,
    "stand_pair_count":4,
    "stand_unit_count":8,
    "coil_spacing_reference_m":4.0,
    "unreal_fit_authority":{"coil_centre_z_m":2.2,"coil_bottom_z_m":1.25,"stand_top_z_m":1.328149,"support_overlap_m":0.078149,"stand_outer_width_m":1.661762},
    "review_focus":["factory-colour cab readability","four-coil longitudinal spacing","coil vertical seating","two stand units per coil","rear-view stand orientation"],
    "owner_decision_required":"APPROVE_APPEARANCE_OR_REQUEST_CHANGES",
    "meshy_credits_used":0
}
with open(os.path.join(OUT,"loaded_lorry_owner_approval_pack_v808.json"),"w",encoding="utf-8") as f:
    json.dump(audit,f,indent=2)
print(json.dumps(audit,indent=2))
