"""Compact S03 rear services and improve full-machine review composition."""
import bpy, hashlib, json, math
from datetime import datetime, timezone
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/PressModulePrototype_v021/CA_MW_PressModulePrototype_v021.blend"
PARENT_SHA="5B954E045DF3EB9807DF88D2BC4191982BFF8F8D47F60512A7A2269808F507CD"
REF=Path(r"C:\Users\greg_\Downloads\ChatGPT Image Aug 7, 2026, 07_52_18 AM.png")
REF_SHA="7F55780C3DF3535C64C126CF71FBB8E5015E8D5540325D38F44B849FDCDB0FE2"
OUT=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/PressModulePrototype_v022"
FBX_DIR=OUT/"FBX"; REVIEW=OUT/"MatchedReview"
BLEND=OUT/"CA_MW_PressModulePrototype_v022.blend"; FBX=FBX_DIR/"SM_CA_MW_PressModulePrototype_v022.fbx"
MANIFEST=OUT/"PRESS_MODULE_PROTOTYPE_MANIFEST_v022.json"; VALIDATION=OUT/"PRESS_MODULE_PROTOTYPE_VALIDATION_v022.json"
for d in (OUT,FBX_DIR,REVIEW): d.mkdir(parents=True,exist_ok=True)
if any(p.exists() for p in (BLEND,FBX,MANIFEST,VALIDATION)): raise RuntimeError("refusing to overwrite v022")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1048576),b""): h.update(c)
    return h.hexdigest().upper()
if sha(PARENT)!=PARENT_SHA or sha(REF)!=REF_SHA: raise RuntimeError("parent/reference hash drift")
bpy.ops.wm.open_mainfile(filepath=str(PARENT))
root=bpy.data.collections.get("CA_MW_PressModulePrototype_v021")
if not root: raise RuntimeError("v021 root missing")
root.name="CA_MW_PressModulePrototype_v022"
old=bpy.data.objects.get("SM_CA_MW_PressModulePrototype_v021")
if old: bpy.data.objects.remove(old,do_unlink=True)
for o in list(root.all_objects): o.name=o.name.replace("v021","v022")
keys=("01_DriveMotorEnclosure","02_CrownCrosshead","03_MainHydraulicCylinders","04_UpperUprights","05_RamSlide","06_GuidesWearPlates","07_BolsterTooling","08_BedPlateFixed","09_TransferClearance","10_LowerUprights","11_HydraulicManifold","12_ElectricalCabinet","13_OperatorHMI","14_SafetyGuarding","15_ServicePlatformAccess","16_FoundationAnchors")
groups={}
for c in root.children:
    c.name=c.name.replace("_v021","_v022")
    for k in keys:
        if c.name.startswith(k): groups[k]=c
if len(groups)!=16: raise RuntimeError("sixteen-group hierarchy missing")
def material(token):
    m=next((x for x in bpy.data.materials if token.lower() in x.name.lower()),None)
    if not m: raise RuntimeError("material missing "+token)
    return m
GREEN,GRAPHITE,STEEL,DARK,YELLOW,COPPER=[material(x) for x in ("CairnwellGreen","FabricatedGraphite","MachinedSteel","DarkMachined","SafetyYellow","CopperService")]
for m,rough,metal in ((GREEN,.48,.70),(GRAPHITE,.56,.76),(STEEL,.30,.88),(DARK,.62,.66),(YELLOW,.46,.48),(COPPER,.34,.84)):
    bs=m.node_tree.nodes.get("Principled BSDF") if m.use_nodes else None
    if bs:
        if "Roughness" in bs.inputs: bs.inputs["Roughness"].default_value=rough
        if "Metallic" in bs.inputs: bs.inputs["Metallic"].default_value=metal
removed=[]
for o in list(root.all_objects):
    if any(t in o.name for t in ("ServiceDrop_","PipeClip_","RearHeader_")):
        removed.append(o.name); bpy.data.objects.remove(o,do_unlink=True)
added=[]
def link(o,g):
    for c in list(o.users_collection): c.objects.unlink(o)
    groups[g].objects.link(o); o["pro_reference_group"]=g; o["engineering_status"]="VISUAL_TBC"; o["collision_intent"]="NoCollision"; o["runtime_authority"]="NONE_SOURCE_ONLY"; added.append(o); return o
def box(n,p,d,m,g,b=.012,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=p,rotation=rot); o=bpy.context.object; o.name=n; o.dimensions=d; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(m)
    if b:
        md=o.modifiers.new("FabricatedEdge","BEVEL"); md.width=min(b,min(d)*.18); md.segments=2
    return link(o,g)
def cyl(n,p,r,depth,m,g,rot=(0,0,0),verts=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=p,rotation=rot); o=bpy.context.object; o.name=n; o.data.materials.append(m); return link(o,g)
def pipe(n,pts,r,m,g):
    cu=bpy.data.curves.new(n+"_Curve","CURVE"); cu.dimensions="3D"; cu.bevel_depth=r; cu.bevel_resolution=2
    sp=cu.splines.new("POLY"); sp.points.add(len(pts)-1)
    for a,b in zip(sp.points,pts): a.co=(*b,1)
    return link(bpy.data.objects.new(n,cu),g)
def label(n,text,p,size,m,g):
    cu=bpy.data.curves.new(n+"_Text","FONT"); cu.body=text; cu.align_x="CENTER"; cu.align_y="CENTER"; cu.size=size; cu.extrude=.006; cu.bevel_depth=.002
    o=bpy.data.objects.new(n,cu); o.location=p; o.rotation_euler=(math.pi/2,0,0); cu.materials.append(m); link(o,g); return o

# Compact service routing is held close to the rear backplate, with short drops
# between bounded panels and two shared horizontal headers.
for i,z in enumerate((3.00,6.18)):
    box(f"S03_CompactHeader_{i}_v022",(0,1.965,z),(3.28,.065,.065),COPPER if i==0 else DARK,keys[10],.008)
for i,x in enumerate((-1.48,-.74,0,.74,1.48)):
    pipe(f"S03_CompactDrop_{i}_v022",[(x,1.975,3.02),(x,1.975,4.48),(x*.92,1.975,4.72)],.023,COPPER if i in (1,3) else DARK,keys[10])
    pipe(f"S03_CompactRise_{i}_v022",[(x*.92,1.975,5.88),(x,1.975,6.16)],.023,DARK,keys[10])
    for z in (3.42,4.18,5.92): box(f"S03_CompactClip_{i}_{z:.2f}_v022",(x,2.005,z),(.09,.025,.035),STEEL,keys[10],.003)
for x in (-1.12,0,1.12):
    box(f"S03_ServiceJunction_{x:+.2f}_v022",(x,1.99,6.62),(.42,.12,.34),GRAPHITE,keys[10],.018)
    for dx in (-.11,.11): cyl(f"S03_JunctionPort_{x:+.2f}_{dx:+.2f}_v022",(x+dx,2.065,6.62),.035,.04,YELLOW,keys[10],(math.pi/2,0,0),16)
box("S03_RearLowerServicePlinth_v022",(0,1.88,2.48),(3.62,.28,.42),GRAPHITE,keys[10],.035)

# Layered fabricated skins, gussets and access doors break the remaining slabs.
for side in (-1,1):
    box(f"S03_CrownSideSkin_{side}_v022",(side*2.28,0,7.34),(.12,3.12,1.28),GRAPHITE,keys[1],.025)
    for y in (-1.25,-.62,0,.62,1.25): box(f"S03_CrownSideRib_{side}_{y:+.2f}_v022",(side*2.35,y,7.34),(.10,.08,1.12),DARK,keys[1],.006)
    box(f"S03_LowerAccessDoor_{side}_v022",(side*1.80,-1.52,1.56),(.58,.05,.92),GRAPHITE,keys[9],.018)
    box(f"S03_LowerAccessLatch_{side}_v022",(side*1.98,-1.56,1.56),(.06,.04,.18),YELLOW,keys[9],.006)
for x in (-1.34,1.34):
    for z in (2.98,3.42,3.86): cyl(f"S03_GuideFastener_{x:+.2f}_{z:.2f}_v022",(x,-1.48,z),.028,.035,STEEL,keys[5],(math.pi/2,0,0),12)

# Readable modelling labels; still presentation-only and not runtime identity.
label("S03_CairnwellText_v022","CAIRNWELL",(0,-1.875,7.59),.20,STEEL,keys[1])
label("S03_StationText_v022","S03",(0,-1.892,6.97),.16,STEEL,keys[1])

source=[]
for c in groups.values(): source.extend(o for o in c.objects if o.type in {"MESH","CURVE","FONT"})
if len(set(o.name for o in source))!=len(source): raise RuntimeError("duplicate names")
bpy.ops.object.select_all(action="DESELECT")
for o in source: o.select_set(True)
bpy.context.view_layer.objects.active=source[0]; bpy.ops.object.duplicate()
for o in list(bpy.context.selected_objects):
    if o.type in {"CURVE","FONT"}: bpy.context.view_layer.objects.active=o; bpy.ops.object.convert(target="MESH")
bpy.ops.object.join(); export=bpy.context.object; export.name="SM_CA_MW_PressModulePrototype_v022"; export.hide_render=True
export["engineering_status"]="VISUAL_TBC"; export["collision_intent"]="NoCollision"; export["runtime_authority"]="NONE_SOURCE_ONLY"
bpy.ops.object.select_all(action="DESELECT"); export.select_set(True); bpy.context.view_layer.objects.active=export
bpy.ops.export_scene.fbx(filepath=str(FBX),use_selection=True,apply_unit_scale=True,apply_scale_options="FBX_SCALE_ALL",axis_forward="-Y",axis_up="Z",use_mesh_modifiers=True,mesh_smooth_type="FACE",add_leaf_bones=False,use_custom_props=True,object_types={"MESH"})

scene=bpy.context.scene; camera=bpy.data.objects.get("PressModule_v021_Camera") or bpy.data.objects.get("PressModule_v022_Camera"); camera.name="PressModule_v022_Camera"
scene.render.resolution_x=1600; scene.render.resolution_y=1200; scene.render.resolution_percentage=100; scene.render.image_settings.file_format="PNG"
def look(o,t): o.rotation_euler=(Vector(t)-o.location).to_track_quat("-Z","Y").to_euler()
views=(("01_full_operator_v022.png",(15,-19,9),(0,0,4.7),66),("02_full_front_v022.png",(0,-22,4.65),(0,0,4.65),68),("03_full_left_v022.png",(-19,0,5.0),(0,0,4.65),68),("04_full_rear_v022.png",(0,22,4.8),(0,0,4.8),68),("05_full_rear_three_quarter_v022.png",(-15,18,9),(0,0,4.8),66))
for fn,loc,target,lens in views:
    camera.location=loc; camera.data.lens=lens; look(camera,target); scene.render.filepath=str(REVIEW/fn); bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND),check_existing=False)
corners=[export.matrix_world@Vector(c) for c in export.bound_box]; dims=[max(p[i] for p in corners)-min(p[i] for p in corners) for i in range(3)]
fail=[]
if len(source)<450: fail.append(f"part count regressed: {len(source)}")
if dims[0]>7.3 or dims[1]>5.1 or dims[2]>9.8: fail.append(f"TBC visual envelope escaped: {dims}")
if FBX.stat().st_size<400000: fail.append("FBX implausibly small")
manifest={"$schema":"cairnwell/source/press-module-prototype-v022/v1","created_utc":datetime.now(timezone.utc).isoformat(),"status":"SOURCE_ONLY_COMPACT_SERVICE_REFINEMENT__VISUAL_REVIEW_REQUIRED__NOT_PROMOTED","parent_sha256":PARENT_SHA,"reference_sha256":REF_SHA,"sheet_id":"CA-AMW-PT-A-S03-REF-01","dimensions_authority":"ALL_TBC","assembly_groups":{k:len(v.objects) for k,v in groups.items()},"authored_part_count":len(source),"removed_cage_parts":len(removed),"added_refinement_parts":len(added),"vertices":len(export.data.vertices),"polygons":len(export.data.polygons),"dimensions_m":dims,"runtime_authority_added":False,"retained_assets_edited":False,"fbx":{"path":"FBX/"+FBX.name,"sha256":sha(FBX),"bytes":FBX.stat().st_size},"renders":["MatchedReview/"+x[0] for x in views]}
MANIFEST.write_text(json.dumps(manifest,indent=2),encoding="utf-8")
validation={"status":"PASS_SOURCE_STRUCTURE__FRESH_VISUAL_DECISION_REQUIRED__NO_UNREAL_IMPORT" if not fail else "FAIL_SOURCE_STRUCTURE__DO_NOT_RETAIN","assembly_group_count":len(groups),"authored_part_count":len(source),"removed_cage_parts":len(removed),"added_refinement_parts":len(added),"vertices":len(export.data.vertices),"polygons":len(export.data.polygons),"dimensions_m":dims,"retained_assets_edited":False,"promotion_authorized":False,"failures":fail}
VALIDATION.write_text(json.dumps(validation,indent=2),encoding="utf-8")
if fail: raise RuntimeError('; '.join(fail))
print(json.dumps(validation,indent=2))
