"""Add reference-led fabrication/service detail to S03 v020; dimensions TBC."""
import bpy, hashlib, json, math
from datetime import datetime, timezone
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/PressModulePrototype_v020/CA_MW_PressModulePrototype_v020.blend"
PARENT_SHA="13E396AB6F24E7887649BFEF0703525F72836DF651B8E6CBCA6C51A9055989C6"
REF=Path(r"C:\Users\greg_\Downloads\ChatGPT Image Aug 7, 2026, 07_52_18 AM.png")
REF_SHA="7F55780C3DF3535C64C126CF71FBB8E5015E8D5540325D38F44B849FDCDB0FE2"
OUT=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/PressModulePrototype_v021"
FBX_DIR=OUT/"FBX"; REVIEW=OUT/"MatchedReview"
BLEND=OUT/"CA_MW_PressModulePrototype_v021.blend"
FBX=FBX_DIR/"SM_CA_MW_PressModulePrototype_v021.fbx"
MANIFEST=OUT/"PRESS_MODULE_PROTOTYPE_MANIFEST_v021.json"
VALIDATION=OUT/"PRESS_MODULE_PROTOTYPE_VALIDATION_v021.json"
for d in (OUT,FBX_DIR,REVIEW): d.mkdir(parents=True,exist_ok=True)
if any(p.exists() for p in (BLEND,FBX,MANIFEST,VALIDATION)): raise RuntimeError("refusing to overwrite v021")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1048576),b""): h.update(c)
    return h.hexdigest().upper()
if sha(PARENT)!=PARENT_SHA or sha(REF)!=REF_SHA: raise RuntimeError("parent/reference hash drift")
bpy.ops.wm.open_mainfile(filepath=str(PARENT))
root=bpy.data.collections.get("CA_MW_PressModulePrototype_v020")
if not root: raise RuntimeError("v020 root missing")
root.name="CA_MW_PressModulePrototype_v021"
old=bpy.data.objects.get("SM_CA_MW_PressModulePrototype_v020")
if old: bpy.data.objects.remove(old,do_unlink=True)
for o in list(root.all_objects): o.name=o.name.replace("v020","v021")
groups={}
keys=("01_DriveMotorEnclosure","02_CrownCrosshead","03_MainHydraulicCylinders","04_UpperUprights","05_RamSlide","06_GuidesWearPlates","07_BolsterTooling","08_BedPlateFixed","09_TransferClearance","10_LowerUprights","11_HydraulicManifold","12_ElectricalCabinet","13_OperatorHMI","14_SafetyGuarding","15_ServicePlatformAccess","16_FoundationAnchors")
for c in root.children:
    c.name=c.name.replace("_v020","_v021")
    for k in keys:
        if c.name.startswith(k): groups[k]=c
if len(groups)!=16: raise RuntimeError(f"expected 16 groups, got {len(groups)}")
def material(token):
    m=next((x for x in bpy.data.materials if token.lower() in x.name.lower()),None)
    if not m: raise RuntimeError("material missing "+token)
    return m
GREEN,GRAPHITE,STEEL,DARK,YELLOW,COPPER=[material(x) for x in ("CairnwellGreen","FabricatedGraphite","MachinedSteel","DarkMachined","SafetyYellow","CopperService")]
added=[]
def link(o,g):
    for c in list(o.users_collection): c.objects.unlink(o)
    groups[g].objects.link(o); o["pro_reference_group"]=g; o["engineering_status"]="VISUAL_TBC"; o["collision_intent"]="NoCollision"; o["runtime_authority"]="NONE_SOURCE_ONLY"; added.append(o); return o
def box(n,p,d,m,g,b=.012):
    bpy.ops.mesh.primitive_cube_add(location=p); o=bpy.context.object; o.name=n; o.dimensions=d; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(m)
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

# Crown seams, fasteners, lifting points and identity surfaces.
for x in (-2.18,-1.46,-.73,0,.73,1.46,2.18): box(f"S03_CrownSeamV_{x:+.2f}_v021",(x,-1.792,7.34),(.025,.025,1.35),DARK,keys[1],.003)
for z in (6.72,7.25,7.92): box(f"S03_CrownSeamH_{z:.2f}_v021",(0,-1.797,z),(4.48,.022,.025),DARK,keys[1],.003)
for x in (-2.02,2.02):
    for z in (6.86,7.18,7.50,7.82): cyl(f"S03_CrownBolt_{x:+.2f}_{z:.2f}_v021",(x,-1.83,z),.035,.035,STEEL,keys[1],(math.pi/2,0,0),16)
for x in (-1.55,1.55):
    cyl(f"S03_LiftingEye_{x:+.2f}_v021",(x,-.35,9.23),.16,.07,YELLOW,keys[1],(math.pi/2,0,0),32)
    cyl(f"S03_LiftingEyeCore_{x:+.2f}_v021",(x,-.39,9.23),.075,.08,DARK,keys[1],(math.pi/2,0,0),24)
box("S03_CairnwellPlate_v021",(0,-1.845,7.58),(1.42,.045,.36),GRAPHITE,keys[1],.018)
box("S03_StationPlate_v021",(0,-1.865,6.96),(.62,.045,.25),DARK,keys[1],.012)

# Drive and upright fabrication details.
for side in (-1,1):
    x=side*1.62
    for z in (6.92,7.35,7.78): cyl(f"S03_DriveHinge_{side}_{z:.2f}_v021",(x-side*.43,-2.10,z),.035,.10,STEEL,keys[0],(math.pi/2,0,0),16)
    box(f"S03_DriveLatch_{side}_v021",(x+side*.30,-2.115,7.48),(.08,.05,.24),YELLOW,keys[0],.008)
    pipe(f"S03_DriveConduit_{side}_v021",[(x,1.26,8.88),(side*2.16,1.26,8.88),(side*2.16,.70,8.15)],.035,DARK,keys[0])
    ux=side*1.80
    for z in (4.28,4.75,5.22,5.69,6.16):
        box(f"S03_UprightRib_{side}_{z:.2f}_v021",(ux,-1.89,z),(.58,.08,.08),GRAPHITE,keys[3],.008)
        for bx in (ux-side*.21,ux+side*.21): cyl(f"S03_UprightBolt_{side}_{bx:+.2f}_{z:.2f}_v021",(bx,-1.95,z),.027,.035,STEEL,keys[3],(math.pi/2,0,0),12)
    for z in (1.08,1.48,1.88): box(f"S03_PedestalRib_{side}_{z:.2f}_v021",(ux,-1.49,z),(.74,.08,.08),GRAPHITE,keys[9],.008)

# Tool clamps, die wear strips and guide blocks.
for x in (-1.15,-.75,-.35,.35,.75,1.15):
    box(f"S03_ToolClamp_{x:+.2f}_v021",(x,-1.30,2.52),(.18,.34,.12),YELLOW,keys[6],.015)
    cyl(f"S03_ClampBolt_{x:+.2f}_v021",(x,-1.49,2.59),.032,.05,STEEL,keys[6],(math.pi/2,0,0),12)
for y in (-.72,0,.72): box(f"S03_DieWearStrip_{y:+.2f}_v021",(0,y,2.66),(2.42,.10,.08),STEEL,keys[6],.008)
for x in (-1.42,1.42): box(f"S03_GuideBlock_{x:+.2f}_v021",(x,-.93,3.18),(.20,.28,.42),DARK,keys[5],.025)

# Dense reference-led rear service face.
for col,x in enumerate((-1.48,-.74,0,.74,1.48)):
    box(f"S03_RearPanel_{col}_v021",(x,1.895,5.30),(.62,.10,1.36),GRAPHITE if col%2==0 else DARK,keys[10],.025)
    for row,z in enumerate((4.80,5.12,5.44,5.76)): cyl(f"S03_RearValve_{col}_{row}_v021",(x,1.975,z),.055,.08,YELLOW if row==0 else STEEL,keys[10],(math.pi/2,0,0),16)
for x in (-1.52,-.92,.92,1.52):
    cyl(f"S03_Filter_{x:+.2f}_v021",(x,2.03,3.22),.16,.62,DARK,keys[10],verts=32)
    cyl(f"S03_FilterCap_{x:+.2f}_v021",(x,2.03,3.56),.19,.10,YELLOW,keys[10],verts=24)
for x in (-.48,.48):
    cyl(f"S03_Accumulator_{x:+.2f}_v021",(x,2.02,3.40),.23,1.08,GRAPHITE,keys[10],verts=40)
    cyl(f"S03_AccumulatorCap_{x:+.2f}_v021",(x,2.02,3.98),.16,.12,STEEL,keys[10])
for i,z in enumerate((2.72,2.96,6.12,6.38)): box(f"S03_RearHeader_{i}_v021",(0,2.00,z),(3.30,.08,.08),COPPER if i%2==0 else DARK,keys[10],.01)
for i,x in enumerate((-1.62,-1.22,-.82,-.42,0,.42,.82,1.22,1.62)):
    pipe(f"S03_ServiceDrop_{i}_v021",[(x,2.02,2.76),(x,2.02,6.34),(x*.72,2.02,6.82)],.025,COPPER if i%3==0 else DARK,keys[10])
    for z in (3.05,4.15,5.25,6.20): box(f"S03_PipeClip_{i}_{z:.2f}_v021",(x,2.06,z),(.10,.035,.035),STEEL,keys[10],.004)
box("S03_RearAccessDoor_v021",(0,1.91,7.40),(1.18,.08,.82),GRAPHITE,keys[10],.025)
box("S03_RearDoorLatch_v021",(.42,1.97,7.40),(.06,.05,.22),YELLOW,keys[10],.008)

# Electrical construction and economical real mesh guarding.
for z in (.92,1.50,2.08,2.66,3.24): box(f"S03_CabinetVent_{z:.2f}_v021",(2.78,-1.235,z),(.58,.028,.12),DARK,keys[11],.006)
box("S03_CabinetIsolator_v021",(3.08,-1.27,2.42),(.12,.06,.30),YELLOW,keys[11],.012)
for side in (-1,1):
    x=side*2.78
    for y0 in (-1.10,0,1.10):
        for j in range(7): box(f"S03_MeshV_{side}_{y0:+.2f}_{j}_v021",(x,y0+j*.18,1.16),(.018,.018,1.74),DARK,keys[13],.002)
        for z in (.38,.60,.82,1.04,1.26,1.48,1.70,1.92): box(f"S03_MeshH_{side}_{y0:+.2f}_{z:.2f}_v021",(x,y0,z),(.018,1.04,.018),DARK,keys[13],.002)
for x in (-3.12,-2.92,-2.72,-2.52,-2.32,-2.12): box(f"S03_Grating_{x:+.2f}_v021",(x,.92,5.81),(.035,1.55,.035),STEEL,keys[14],.002)

source=[]
for c in groups.values(): source.extend(o for o in c.objects if o.type in {"MESH","CURVE"})
if len(set(o.name for o in source))!=len(source): raise RuntimeError("duplicate names")
bpy.ops.object.select_all(action="DESELECT")
for o in source: o.select_set(True)
bpy.context.view_layer.objects.active=source[0]; bpy.ops.object.duplicate()
for o in list(bpy.context.selected_objects):
    if o.type=="CURVE": bpy.context.view_layer.objects.active=o; bpy.ops.object.convert(target="MESH")
bpy.ops.object.join(); export=bpy.context.object; export.name="SM_CA_MW_PressModulePrototype_v021"; export.hide_render=True
export["engineering_status"]="VISUAL_TBC"; export["collision_intent"]="NoCollision"; export["runtime_authority"]="NONE_SOURCE_ONLY"
bpy.ops.object.select_all(action="DESELECT"); export.select_set(True); bpy.context.view_layer.objects.active=export
bpy.ops.export_scene.fbx(filepath=str(FBX),use_selection=True,apply_unit_scale=True,apply_scale_options="FBX_SCALE_ALL",axis_forward="-Y",axis_up="Z",use_mesh_modifiers=True,mesh_smooth_type="FACE",add_leaf_bones=False,use_custom_props=True,object_types={"MESH"})

scene=bpy.context.scene; camera=bpy.data.objects.get("PressModule_v020_Camera") or bpy.data.objects.get("PressModule_v021_Camera"); camera.name="PressModule_v021_Camera"
scene.render.resolution_x=1600; scene.render.resolution_y=1200; scene.render.resolution_percentage=100; scene.render.image_settings.file_format="PNG"
def look(o,t): o.rotation_euler=(Vector(t)-o.location).to_track_quat("-Z","Y").to_euler()
views=(("01_operator_v021.png",(12,-15,8),(0,0,4.7),62),("02_front_v021.png",(0,-18,4.7),(0,0,4.7),68),("03_left_v021.png",(-15,0,5.2),(0,0,4.7),68),("04_rear_v021.png",(0,18,4.9),(0,0,4.9),68),("05_rear_three_quarter_v021.png",(-11,14,7),(0,0,4.8),62))
for fn,loc,target,lens in views:
    camera.location=loc; camera.data.lens=lens; look(camera,target); scene.render.filepath=str(REVIEW/fn); bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND),check_existing=False)
corners=[export.matrix_world@Vector(c) for c in export.bound_box]; dims=[max(p[i] for p in corners)-min(p[i] for p in corners) for i in range(3)]
fail=[]
if len(source)<400: fail.append(f"detail density too low: {len(source)}")
if dims[0]>7.3 or dims[1]>5.1 or dims[2]>9.8: fail.append(f"TBC visual envelope escaped: {dims}")
if FBX.stat().st_size<400000: fail.append("FBX implausibly small")
manifest={"$schema":"cairnwell/source/press-module-prototype-v021/v1","created_utc":datetime.now(timezone.utc).isoformat(),"status":"SOURCE_ONLY_PRO_DETAIL_REFINEMENT__VISUAL_REVIEW_REQUIRED__NOT_PROMOTED","parent_sha256":PARENT_SHA,"reference_sha256":REF_SHA,"sheet_id":"CA-AMW-PT-A-S03-REF-01","dimensions_authority":"ALL_TBC","assembly_groups":{k:len(v.objects) for k,v in groups.items()},"authored_part_count":len(source),"added_detail_parts":len(added),"vertices":len(export.data.vertices),"polygons":len(export.data.polygons),"dimensions_m":dims,"runtime_authority_added":False,"retained_assets_edited":False,"fbx":{"path":"FBX/"+FBX.name,"sha256":sha(FBX),"bytes":FBX.stat().st_size},"renders":["MatchedReview/"+x[0] for x in views]}
MANIFEST.write_text(json.dumps(manifest,indent=2),encoding="utf-8")
validation={"status":"PASS_SOURCE_STRUCTURE__FRESH_VISUAL_DECISION_REQUIRED__NO_UNREAL_IMPORT" if not fail else "FAIL_SOURCE_STRUCTURE__DO_NOT_RETAIN","assembly_group_count":len(groups),"authored_part_count":len(source),"added_detail_parts":len(added),"vertices":len(export.data.vertices),"polygons":len(export.data.polygons),"dimensions_m":dims,"retained_assets_edited":False,"promotion_authorized":False,"failures":fail}
VALIDATION.write_text(json.dumps(validation,indent=2),encoding="utf-8")
if fail: raise RuntimeError('; '.join(fail))
print(json.dumps(validation,indent=2))
