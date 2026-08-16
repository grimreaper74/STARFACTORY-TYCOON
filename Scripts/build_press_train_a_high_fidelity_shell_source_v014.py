"""Build a non-destructive high-detail fixed shell for the retained Train A mechanics.

The source adds presentation-only fabricated housings and service equipment. It
does not replace, resize or edit the retained v013 actors, moving parts, pivots,
collision authorities or runtime metadata. Values are visual/detail decisions
inside the already-authorised stage envelopes, not construction data.
"""
import bpy
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/PresentationShell_v014"
FBX_DIR = OUT / "FBX"
RENDERS = OUT / "Renders"
BLEND_OUT = OUT / "CA_MW_PressTrainA_PresentationShell_v014.blend"
FBX_OUT = FBX_DIR / "SM_CA_MW_PTA_PresentationShell_v014.fbx"
MANIFEST = OUT / "PRESS_TRAIN_A_PRESENTATION_SHELL_MANIFEST_v014.json"
VALIDATION = OUT / "PRESS_TRAIN_A_PRESENTATION_SHELL_VALIDATION_v014.json"
PARENT = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/AssemblyStudy_v013/CA_MW_PressTrainA_AssemblyStudy_v013.blend"
for p in (OUT, FBX_DIR, RENDERS): p.mkdir(parents=True, exist_ok=True)
if any(p.exists() for p in (BLEND_OUT, FBX_OUT, MANIFEST, VALIDATION)):
    raise RuntimeError("Refusing to overwrite immutable PresentationShell_v014 outputs")

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024), b""): h.update(b)
    return h.hexdigest().upper()

bpy.ops.wm.open_mainfile(filepath=str(PARENT))
scene=bpy.context.scene
shell=bpy.data.collections.new("PTA_PRESENTATION_SHELL_V014")
scene.collection.children.link(shell)

def mat(name,color,metal,rough):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.metallic=metal; m.roughness=rough; m.use_nodes=True
    bs=m.node_tree.nodes.get("Principled BSDF"); bs.inputs["Base Color"].default_value=(*color,1); bs.inputs["Metallic"].default_value=metal; bs.inputs["Roughness"].default_value=rough
    return m
M={
 "charcoal":mat("CA_MW_PTA_Shell_FoundryCharcoal_v014",(0.055,0.07,0.08),0.62,0.31),
 "green":mat("CA_MW_PTA_Shell_CairnwellGreen_v014",(0.025,0.19,0.13),0.38,0.3),
 "steel":mat("CA_MW_PTA_Shell_WorkedSteel_v014",(0.27,0.31,0.34),0.83,0.23),
 "darksteel":mat("CA_MW_PTA_Shell_DarkMachinedSteel_v014",(0.09,0.11,0.13),0.78,0.2),
 "yellow":mat("CA_MW_PTA_Shell_SafetyYellow_v014",(0.93,0.57,0.025),0.35,0.28),
 "rubber":mat("CA_MW_PTA_Shell_IndustrialRubber_v014",(0.018,0.022,0.025),0.08,0.58),
 "glass":mat("CA_MW_PTA_Shell_InspectionGlass_v014",(0.025,0.19,0.2),0.3,0.16),
}
made=[]
def link_only(obj):
    for c in list(obj.users_collection): c.objects.unlink(obj)
    shell.objects.link(obj)
def cube(name,loc,dims,material,bevel=.04):
    bpy.ops.mesh.primitive_cube_add(location=loc); o=bpy.context.object; o.name=name; o.dimensions=dims; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); link_only(o); o.data.materials.append(material)
    if bevel:
        md=o.modifiers.new("FabricationRadius","BEVEL"); md.width=min(bevel,min(dims)*.22); md.segments=4
    made.append(o); return o
def cyl(name,loc,r,depth,material,rot=(0,math.pi/2,0),verts=48,bevel=.025):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=loc,rotation=rot); o=bpy.context.object; o.name=name; link_only(o); o.data.materials.append(material)
    md=o.modifiers.new("MachinedEdge","BEVEL"); md.width=bevel; md.segments=3; made.append(o); return o
def pipe(name,points,r,material):
    curve=bpy.data.curves.new(name,"CURVE"); curve.dimensions="3D"; curve.bevel_depth=r; curve.bevel_resolution=3; curve.resolution_u=2
    spline=curve.splines.new("POLY"); spline.points.add(len(points)-1)
    for p,co in zip(spline.points,points): p.co=(*co,1)
    o=bpy.data.objects.new(name,curve); shell.objects.link(o); o.data.materials.append(material); made.append(o); return o

stages=[("S02",7.5,10.5,2.55),("S03",15.0,8.2,2.30),("S04",22.5,8.2,2.30),("S05",30.0,8.2,2.30),("S06",37.5,8.2,2.30)]
for idx,(s,y,h,half_y) in enumerate(stages):
    outer_x=4.42 if s=="S02" else 4.25
    crown_z=h-0.55
    # Rounded operator-side crown shell, layered cap and vertical side cheeks.
    cube(f"{s}_CrownMain",(outer_x,y,crown_z),(0.28,half_y*1.92,1.15),M["charcoal"],.12)
    cube(f"{s}_CrownGreenBand",(outer_x+.155,y,crown_z-.10),(.06,half_y*1.70,.24),M["green"],.035)
    cube(f"{s}_CrownTopCap",(outer_x+.02,y,crown_z+.67),(.34,half_y*1.72,.20),M["steel"],.07)
    for side in (-1,1):
        sy=y+side*(half_y-.16)
        cube(f"{s}_Cheek_{side}",(outer_x,sy,h*.51),(.30,.34,h*.70),M["charcoal"],.10)
        cube(f"{s}_CheekWear_{side}",(outer_x+.165,sy,h*.51),(.055,.20,h*.50),M["steel"],.025)
        # Large real-machine drive/motor cues at crown ends.
        cyl(f"{s}_EccentricHousing_{side}",(outer_x+.24,sy,crown_z),.52,.22,M["darksteel"])
        cyl(f"{s}_EccentricHub_{side}",(outer_x+.38,sy,crown_z),.23,.14,M["steel"])
        cyl(f"{s}_HubCap_{side}",(outer_x+.47,sy,crown_z),.10,.055,M["yellow"])
    # Segmented access doors and inset inspection panels instead of a monolithic facade.
    door_z=3.25 if s=="S02" else 2.85
    for j,dy in enumerate((-1.55,0,1.55)):
        cube(f"{s}_ServiceDoor_{j}",(outer_x+.18,y+dy,door_z),(.08,1.25,2.25),M["steel"],.055)
        cube(f"{s}_DoorInset_{j}",(outer_x+.228,y+dy,door_z),(.025,.95,1.62),M["charcoal"],.03)
        cube(f"{s}_DoorHandle_{j}",(outer_x+.26,y+dy+.39,door_z),(.05,.08,.46),M["yellow"],.025)
        for rz in (-.72,.72):
            for ry in (-.43,.43): cyl(f"{s}_DoorBolt_{j}_{rz}_{ry}",(outer_x+.27,y+dy+ry,door_z+rz),.032,.045,M["steel"],verts=24,bevel=.008)
    # Horizontal fabrication ribs break the slab silhouette.
    for k,z in enumerate((1.35,5.15,h-1.7)):
        cube(f"{s}_FrameRib_{k}",(outer_x+.17,y,z),(.08,half_y*1.74,.18),M["green"],.035)
    # Operator-side manifold: pipes, valves, pressure vessels and guarded service deck.
    mech_y=y-half_y-.62
    cube(f"{s}_ManifoldCabinet",(outer_x-.05,mech_y,1.35),(.55,1.05,2.05),M["darksteel"],.08)
    for q,z in enumerate((.72,1.15,1.58,2.0)):
        pipe(f"{s}_HydraulicLine_{q}",[(outer_x+.28,mech_y-.34,z),(outer_x+.38,mech_y+.18,z),(outer_x+.38,y-half_y+.18,z+.30)],.032,M["steel"])
        cyl(f"{s}_Valve_{q}",(outer_x+.42,mech_y-.38,z),.105,.10,M["yellow"],rot=(0,math.pi/2,0),verts=32,bevel=.012)
    for q,dy in enumerate((-.28,.28)):
        cyl(f"{s}_PressureVessel_{q}",(outer_x-.18,mech_y+dy,2.85),.22,1.35,M["steel"],rot=(0,0,0),verts=40)
    # Roof cooling/fan housings and lifting eyes.
    for q,dy in enumerate((-.72,.72)):
        cyl(f"{s}_RoofFan_{q}",(outer_x-.15,y+dy,h+.02),.32,.18,M["darksteel"],rot=(0,0,0),verts=48)
        cyl(f"{s}_RoofFanGuard_{q}",(outer_x-.15,y+dy,h+.13),.25,.06,M["steel"],rot=(0,0,0),verts=32,bevel=.01)
    # Stage identity plaque surface (text remains separate/authoritative in Unreal).
    cube(f"{s}_IdentityBacker",(outer_x+.235,y,crown_z-.62),(.045,1.20,.34),M["green"],.045)

# Join into one fixed non-colliding presentation asset, retaining material slots.
bpy.ops.object.select_all(action="DESELECT")
for o in made:
    o.select_set(True)
    bpy.context.view_layer.objects.active=o
bpy.ops.object.convert(target="MESH")
bpy.ops.object.join()
asset=bpy.context.object; asset.name="SM_CA_MW_PTA_PresentationShell_v014"
asset["role"]="fixed_visual_presentation_shell"
asset["collision_intent"]="NoCollision"
asset["runtime_authority"]="retained_v027_v034_components_only"
asset["engineering_status"]="GAME_VISUAL_DETAIL_WITHIN_AUTHORISED_ENVELOPES_TBC"

# Keep coordinates baked and set asset origin at assembly datum.
bpy.context.scene.cursor.location=(0,0,0)
bpy.ops.object.origin_set(type="ORIGIN_CURSOR")

bpy.ops.object.select_all(action="DESELECT"); asset.select_set(True); bpy.context.view_layer.objects.active=asset
bpy.ops.export_scene.fbx(filepath=str(FBX_OUT),use_selection=True,apply_unit_scale=True,apply_scale_options="FBX_SCALE_ALL",axis_forward="-Y",axis_up="Z",use_mesh_modifiers=True,mesh_smooth_type="FACE",add_leaf_bones=False,use_custom_props=True,object_types={"MESH"})

# Evidence renders include the retained source plus the overlay.
scene.render.engine="BLENDER_EEVEE"; scene.render.resolution_x=1600; scene.render.resolution_y=900; scene.render.resolution_percentage=100; scene.render.image_settings.file_format="PNG"; scene.view_settings.look="AgX - Medium High Contrast"; scene.world.color=(.012,.016,.02)
def look(obj,target): obj.rotation_euler=(Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()
camd=bpy.data.cameras.new("PTA_v014_Camera"); cam=bpy.data.objects.new("PTA_v014_Camera",camd); scene.collection.objects.link(cam); scene.camera=cam
for name,loc,target,energy,size in (("Key",(14,-1,13),(0,23,4),1900,7),("Rim",(-11,30,14),(0,23,4),1500,8),("Roof",(5,23,17),(0,23,3),2100,10)):
    ld=bpy.data.lights.new("PTA_v014_"+name,"AREA"); ld.energy=energy; ld.shape="DISK"; ld.size=size; lo=bpy.data.objects.new("PTA_v014_"+name,ld); scene.collection.objects.link(lo); lo.location=loc; look(lo,target)
def render(name,loc,target,lens):
    cam.location=loc; cam.data.lens=lens; look(cam,target); scene.render.filepath=str(RENDERS/name); bpy.ops.render.render(write_still=True)
render("01_operator_shell_v014.png",(15,-4,7.2),(2.2,23,4.1),54)
render("02_mid_train_service_detail_v014.png",(11,17,5.1),(3.5,23,3.6),62)
render("03_management_shell_v014.png",(18,18,13),(1.5,23,3.9),55)

bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_OUT),check_existing=False)
polys=len(asset.data.polygons); verts=len(asset.data.vertices)
manifest={
 "$schema":"cairnwell/source/press-train-presentation-shell-v014/v1",
 "created_utc":datetime.now(timezone.utc).isoformat(),
 "status":"SOURCE_ONLY_HIGH_DETAIL_FIXED_SHELL__UNREAL_INTAKE_REQUIRED__NOT_PROMOTED",
 "parent_v013_sha256":sha(PARENT),"asset_name":asset.name,"source_part_count_before_join":len(made),
 "vertices":verts,"polygons":polys,"material_slots":[m.name for m in asset.data.materials],
 "stage_coverage":[s[0] for s in stages],"collision_intent":"NoCollision",
 "retained_authorities_edited":False,"moving_parts_duplicated":False,"unverified_engineering_values_adopted":False,
 "fbx":{"file":"FBX/"+FBX_OUT.name,"bytes":FBX_OUT.stat().st_size,"sha256":sha(FBX_OUT)},
 "renders":["Renders/01_operator_shell_v014.png","Renders/02_mid_train_service_detail_v014.png","Renders/03_management_shell_v014.png"]
}
MANIFEST.write_text(json.dumps(manifest,indent=2),encoding="utf-8")
validation={"status":"PASS__V014_FIXED_PRESENTATION_SHELL_SOURCE__UNREAL_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED","asset_count":1,"stage_count":5,"source_part_count":len(made),"vertices":verts,"polygons":polys,"collision_intent":"NoCollision","retained_authorities_edited":False,"promotion_authorized":False}
VALIDATION.write_text(json.dumps(validation,indent=2),encoding="utf-8")
print(json.dumps(validation,indent=2))
