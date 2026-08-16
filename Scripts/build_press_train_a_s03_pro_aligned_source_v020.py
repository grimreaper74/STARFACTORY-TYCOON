"""Rebuild S03 source around the accepted Pro sixteen-assembly visual contract.

All dimensions remain TBC visual proportions. This source adds no collision,
navigation, mover, safety, recipe or runtime authority.
"""
import bpy, hashlib, json, math
from datetime import datetime, timezone
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/PressModulePrototype_v019/CA_MW_PressModulePrototype_v019.blend"
PARENT_SHA="DA1DFE83248BCA17E8BFB57F809B7F28EF58F6217A38D3DAF0FB97F328913B4D"
REFERENCE=Path(r"C:\Users\greg_\Downloads\ChatGPT Image Aug 7, 2026, 07_52_18 AM.png")
REFERENCE_SHA="7F55780C3DF3535C64C126CF71FBB8E5015E8D5540325D38F44B849FDCDB0FE2"
OUT=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/PressModulePrototype_v020"
FBX_DIR=OUT/"FBX"; RENDERS=OUT/"Renders"
BLEND_OUT=OUT/"CA_MW_PressModulePrototype_v020.blend"
FBX_OUT=FBX_DIR/"SM_CA_MW_PressModulePrototype_v020.fbx"
MANIFEST=OUT/"PRESS_MODULE_PROTOTYPE_MANIFEST_v020.json"
VALIDATION=OUT/"PRESS_MODULE_PROTOTYPE_VALIDATION_v020.json"
for d in (OUT,FBX_DIR,RENDERS): d.mkdir(parents=True,exist_ok=True)
if any(p.exists() for p in (BLEND_OUT,FBX_OUT,MANIFEST,VALIDATION)): raise RuntimeError("refusing to overwrite v020")
def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as s:
        for c in iter(lambda:s.read(1024*1024),b""): h.update(c)
    return h.hexdigest().upper()
if sha(PARENT)!=PARENT_SHA or sha(REFERENCE)!=REFERENCE_SHA: raise RuntimeError("parent/reference hash drift")
bpy.ops.wm.open_mainfile(filepath=str(PARENT))
scene=bpy.context.scene
root=bpy.data.collections.get("CA_MW_PressModulePrototype_v019")
if root is None: raise RuntimeError("v019 collection missing")
root.name="CA_MW_PressModulePrototype_v020"
old=bpy.data.objects.get("SM_CA_MW_PressModulePrototype_v019")
if old is None: raise RuntimeError("v019 export missing")
bpy.data.objects.remove(old,do_unlink=True)
for o in list(root.objects): o.name=o.name.replace("v019","v020")
for m in bpy.data.materials:
    if "v019" in m.name: m.name=m.name.replace("v019","v020")
def mat(token):
    value=next((m for m in bpy.data.materials if token.lower() in m.name.lower()),None)
    if value is None: raise RuntimeError("material missing "+token)
    return value
GREEN,GRAPHITE,STEEL,DARK,YELLOW,COPPER=[mat(x) for x in ("CairnwellGreen","FabricatedGraphite","MachinedSteel","DarkMachined","SafetyYellow","CopperService")]

# Re-proportion the inherited modular core toward the deeper Pro side/top views.
structural_tokens=("Foundation","Lower_Frame","Bolster","Upright","Crown","Ram","Die","DriveGuard","DrivePlinth","TransferRail","TransferRoller")
for o in list(root.objects):
    if o.type not in {"MESH","CURVE"}: continue
    if any(t in o.name for t in structural_tokens):
        if o.type=="MESH":
            o.dimensions.y*=1.42
            bpy.context.view_layer.objects.active=o
            o.select_set(True); bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.select_set(False)
        if abs(o.location.y)>.25: o.location.y*=1.42

groups=[
"01_DriveMotorEnclosure","02_CrownCrosshead","03_MainHydraulicCylinders","04_UpperUprights",
"05_RamSlide","06_GuidesWearPlates","07_BolsterTooling","08_BedPlateFixed",
"09_TransferClearance","10_LowerUprights","11_HydraulicManifold","12_ElectricalCabinet",
"13_OperatorHMI","14_SafetyGuarding","15_ServicePlatformAccess","16_FoundationAnchors"]
collections={}
for name in groups:
    c=bpy.data.collections.new(name+"_v020"); root.children.link(c); collections[name]=c
added=[]
def link(obj,group):
    for owner in list(obj.users_collection): owner.objects.unlink(obj)
    collections[group].objects.link(obj)
    obj["pro_reference_group"]=group; obj["engineering_status"]="VISUAL_MODELLING_REFERENCE_TBC"; obj["collision_intent"]="NoCollision"; obj["runtime_authority"]="NONE_SOURCE_ONLY"
def box(name,loc,dims,material,group,bevel=.035,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc,rotation=rot); o=bpy.context.object; o.name=name; o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(material)
    if bevel:
        mod=o.modifiers.new("FabricatedEdge","BEVEL"); mod.width=min(bevel,min(dims)*.16); mod.segments=3
    link(o,group); added.append(o); return o
def cyl(name,loc,radius,depth,material,group,rot=(math.pi/2,0,0),verts=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=radius,depth=depth,location=loc,rotation=rot); o=bpy.context.object; o.name=name; o.data.materials.append(material)
    mod=o.modifiers.new("MachinedEdge","BEVEL"); mod.width=min(.016,radius*.1); mod.segments=3
    link(o,group); added.append(o); return o
def pipe(name,points,radius,material,group):
    curve=bpy.data.curves.new(name+"_Curve","CURVE"); curve.dimensions="3D"; curve.bevel_depth=radius; curve.bevel_resolution=3
    spline=curve.splines.new("POLY"); spline.points.add(len(points)-1)
    for p,xyz in zip(spline.points,points): p.co=(*xyz,1)
    o=bpy.data.objects.new(name,curve); curve.materials.append(material); link(o,group); added.append(o); return o

# Assign retained components to the nearest explicit Pro assembly group.
def choose(name):
    if any(x in name for x in ("Drive","Motor","Flywheel")): return groups[0]
    if "Crown" in name or "Bearing" in name or "TiePlate" in name: return groups[1]
    if "TieRod" in name: return groups[2]
    if "Upright" in name and "Lower" not in name: return groups[3]
    if "Ram" in name: return groups[4]
    if "Guide" in name or "WearPlate" in name: return groups[5]
    if "Die" in name or "Bolster" in name: return groups[6]
    if "Lower_Frame" in name: return groups[7]
    if "Transfer" in name: return groups[8]
    if "FootGusset" in name or "Lower" in name: return groups[9]
    if any(x in name for x in ("Manifold","Valve","Hydraulic","Supply","Return")): return groups[10]
    if "ServiceCabinet" in name: return groups[11]
    if "HMI" in name: return groups[12]
    if any(x in name for x in ("Guard","Fence")): return groups[13]
    if "Ladder" in name or "Platform" in name: return groups[14]
    return groups[15]
for o in list(root.objects):
    if o.type in {"MESH","CURVE"}: link(o,choose(o.name))

# 01/02: massive enclosed upper machine with asymmetric side drive housings.
box("S03_Pro_CrownMain_v020",(0,0,7.30),(4.62,3.46,1.72),GREEN,groups[1],.08)
box("S03_Pro_CrownFrontSkin_v020",(0,-1.755,7.32),(2.22,.055,1.28),GREEN,groups[1],.025)
for side in (-1,1):
    box(f"S03_Pro_FrontDriveCabinet_{side}_v020",(side*1.62,-1.82,7.48),(1.06,.48,1.68),GRAPHITE,groups[0],.055)
    box(f"S03_Pro_DriveDoor_{side}_v020",(side*1.62,-2.068,7.48),(.82,.035,1.37),DARK,groups[0],.018)
    for z in (7.10,7.34,7.58,7.82): box(f"S03_Pro_DriveVent_{side}_{z:.2f}_v020",(side*1.62,-2.09,z),(.60,.022,.055),STEEL,groups[0],.006)
box("S03_Pro_TopDriveEnclosure_v020",(0,.18,8.65),(3.72,3.08,1.02),GRAPHITE,groups[0],.07)
cyl("S03_Pro_SideFlywheelGuard_v020",(-2.37,.45,7.92),.70,.32,DARK,groups[0],rot=(0,math.pi/2,0),verts=64)
cyl("S03_Pro_SideFlywheelHub_v020",(-2.55,.45,7.92),.22,.06,STEEL,groups[0],rot=(0,math.pi/2,0))

# 03: twin hydraulic cylinders visually connect crown to the ram.
for x in (-.82,.82):
    cyl(f"S03_Pro_HydraulicCylinder_{x:+.2f}_v020",(x,0,6.18),.22,1.72,DARK,groups[2],rot=(0,0,0))
    cyl(f"S03_Pro_HydraulicRod_{x:+.2f}_v020",(x,0,5.25),.105,.72,STEEL,groups[2],rot=(0,0,0))

# 04/10: broad cheek plates and lower pedestal courses add the reference mass.
for side in (-1,1):
    box(f"S03_Pro_UpperCheek_{side}_v020",(side*1.80,-1.52,5.42),(.66,.34,2.72),GREEN,groups[3],.055)
    box(f"S03_Pro_UpperServicePanel_{side}_v020",(side*1.80,-1.705,5.42),(.48,.025,2.30),GRAPHITE,groups[3],.018)
    box(f"S03_Pro_LowerPedestal_{side}_v020",(side*1.78,0,1.52),(.82,2.88,1.64),GREEN,groups[9],.07)
    box(f"S03_Pro_LowerWearFace_{side}_v020",(side*1.34,-1.45,1.62),(.08,.20,1.10),STEEL,groups[9],.018)

# 05-09: dense, guarded process throat with explicit fixed/moving visual layers.
box("S03_Pro_RamFrontApron_v020",(0,-1.54,4.94),(2.82,.24,.88),GREEN,groups[4],.045)
for x in (-1.28,1.28): box(f"S03_Pro_SlideGuideTower_{x:+.2f}_v020",(x,-1.30,4.38),(.24,.32,1.72),DARK,groups[5],.025)
box("S03_Pro_ToolingUpper_v020",(0,-.05,4.30),(2.72,2.02,.38),DARK,groups[6],.035)
box("S03_Pro_ToolingLower_v020",(0,-.05,2.18),(2.86,2.08,.44),STEEL,groups[6],.035)
box("S03_Pro_BedPlate_v020",(0,0,1.78),(3.50,3.00,.36),GRAPHITE,groups[7],.045)
for x in (-1.20,-.60,0,.60,1.20): box(f"S03_Pro_BolsterSlot_{x:+.2f}_v020",(x,-1.53,2.44),(.07,.08,.05),DARK,groups[6],.005)
box("S03_Pro_TransferHeader_v020",(0,-1.72,3.54),(3.18,.10,.12),YELLOW,groups[8],.018)
for x in (-1.35,-.90,-.45,0,.45,.90,1.35):
    cyl(f"S03_Pro_TransferTool_{x:+.2f}_v020",(x,-1.80,3.37),.055,.30,STEEL,groups[8],rot=(math.pi/2,0,0),verts=24)

# 11: rear hydraulic wall and dense ordered service routing.
box("S03_Pro_RearServiceBackplate_v020",(0,1.78,4.55),(3.70,.14,4.65),GREEN,groups[10],.035)
for side in (-1,1):
    box(f"S03_Pro_RearManifold_{side}_v020",(side*1.15,1.92,4.18),(.72,.30,1.45),GRAPHITE,groups[10],.045)
    for i,z in enumerate((3.78,4.05,4.32,4.59)):
        cyl(f"S03_Pro_RearValve_{side}_{i}_v020",(side*1.15,2.09,z),.075,.09,YELLOW,groups[10],rot=(math.pi/2,0,0),verts=24)
    for offset in (-.26,0,.26):
        x=side*1.15+offset
        pipe(f"S03_Pro_RearPipe_{side}_{offset:+.2f}_v020",[(x,2.02,3.30),(x,2.02,6.48),(side*.70,2.02,6.88)],.032,COPPER if offset==0 else DARK,groups[10])

# 12/13: separate cabinet and operator console, as shown in the orthographics.
box("S03_Pro_ElectricalCabinet_v020",(2.78,-.62,2.28),(1.02,1.12,3.55),GRAPHITE,groups[11],.055)
box("S03_Pro_ElectricalDoor_v020",(2.78,-1.195,2.28),(.80,.035,3.15),STEEL,groups[11],.018)
for z in (1.25,1.55,1.85): box(f"S03_Pro_CabinetVent_{z:.2f}_v020",(2.78,-1.22,z),(.54,.022,.07),DARK,groups[11],.006)
box("S03_Pro_HMI_Pedestal_v020",(3.15,-1.72,1.18),(.34,.38,2.12),GRAPHITE,groups[12],.045)
box("S03_Pro_HMI_Console_v020",(3.15,-1.82,2.42),(.88,.34,.72),DARK,groups[12],.055,rot=(math.radians(-12),0,0))
box("S03_Pro_HMI_Display_v020",(3.15,-2.00,2.49),(.58,.025,.38),STEEL,groups[12],.018,rot=(math.radians(-12),0,0))

# 14/15: fenced operator cell and side/rear maintenance platforms.
for side in (-1,1):
    box(f"S03_Pro_SideFenceBase_{side}_v020",(side*2.78,0,.45),(1.20,3.36,.08),YELLOW,groups[13],.015)
    for y in (-1.65,-.55,.55,1.65): box(f"S03_Pro_FencePost_{side}_{y:+.2f}_v020",(side*2.78,y,1.15),(.07,.07,2.24),YELLOW,groups[13],.018)
    for z in (.55,1.18,1.78): box(f"S03_Pro_FenceRail_{side}_{z:.2f}_v020",(side*2.78,0,z),(.07,3.28,.07),YELLOW,groups[13],.018)
box("S03_Pro_ServicePlatform_v020",(-2.62,.92,5.72),(1.24,1.72,.15),GRAPHITE,groups[14],.025)
for x in (-3.18,-2.06): box(f"S03_Pro_PlatformRail_{x:+.2f}_v020",(x,.92,6.30),(.07,1.68,1.18),YELLOW,groups[14],.018)
for z in (1.55,2.15,2.75,3.35,3.95,4.55,5.15): box(f"S03_Pro_AccessRung_{z:.2f}_v020",(-3.18,1.70,z),(.46,.07,.055),YELLOW,groups[14],.015)
for x in (-3.39,-2.97): box(f"S03_Pro_AccessRail_{x:+.2f}_v020",(x,1.70,3.35),(.055,.07,4.18),YELLOW,groups[14],.015)

# 16: expanded foundation with visible anchor schedule, still TBC visual geometry.
box("S03_Pro_FoundationMat_v020",(0,0,.10),(6.35,4.45,.20),GRAPHITE,groups[15],.055)
box("S03_Pro_AnchorPlate_v020",(0,0,.25),(5.20,3.72,.16),GREEN,groups[15],.045)
for x in (-2.30,-1.15,0,1.15,2.30):
    for y in (-1.62,1.62): cyl(f"S03_Pro_Anchor_{x:+.2f}_{y:+.2f}_v020",(x,y,.40),.045,.20,STEEL,groups[15],rot=(0,0,0),verts=24)

source_parts=[]
for c in collections.values(): source_parts.extend([o for o in c.objects if o.type in {"MESH","CURVE"}])
if len(set(o.name for o in source_parts))!=len(source_parts): raise RuntimeError("duplicate source object names")
bpy.ops.object.select_all(action="DESELECT")
for o in source_parts: o.select_set(True)
bpy.context.view_layer.objects.active=source_parts[0]; bpy.ops.object.duplicate()
dupes=list(bpy.context.selected_objects)
for o in dupes:
    if o.type=="CURVE": bpy.context.view_layer.objects.active=o; bpy.ops.object.convert(target="MESH")
bpy.ops.object.join(); export=bpy.context.object; export.name="SM_CA_MW_PressModulePrototype_v020"; export.hide_render=True
export["engineering_status"]="VISUAL_MODELLING_REFERENCE_TBC"; export["collision_intent"]="NoCollision"; export["runtime_authority"]="RETAINED_NATIVE_STATION_ONLY"
bpy.ops.object.select_all(action="DESELECT"); export.select_set(True); bpy.context.view_layer.objects.active=export
bpy.ops.export_scene.fbx(filepath=str(FBX_OUT),use_selection=True,apply_unit_scale=True,apply_scale_options="FBX_SCALE_ALL",axis_forward="-Y",axis_up="Z",use_mesh_modifiers=True,mesh_smooth_type="FACE",add_leaf_bones=False,use_custom_props=True,object_types={"MESH"})

scene.render.resolution_x=1600; scene.render.resolution_y=1200; scene.render.resolution_percentage=100; scene.render.image_settings.file_format="PNG"
camera=bpy.data.objects.get("PressModule_v019_Camera"); camera.name="PressModule_v020_Camera"
def look(o,target): o.rotation_euler=(Vector(target)-o.location).to_track_quat("-Z","Y").to_euler()
bpy.ops.mesh.primitive_plane_add(size=30,location=(0,0,-.02)); floor=bpy.context.object; floor.name="ReviewOnlyFloor_v020"; floor.data.materials.append(GRAPHITE)
views=[
 ("01_operator_three_quarter_v020.png",(12,-15,8),(0,0,4.7),62),
 ("02_front_operator_v020.png",(0,-18,4.7),(0,0,4.7),68),
 ("03_left_service_v020.png",(-13,0,5.1),(0,0,4.6),66),
 ("04_rear_service_v020.png",(0,18,4.8),(0,0,4.8),68)]
for filename,loc,target,lens in views:
    camera.location=loc; camera.data.lens=lens; look(camera,target); scene.render.filepath=str(RENDERS/filename); bpy.ops.render.render(write_still=True)
bpy.data.objects.remove(floor,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_OUT),check_existing=False)
corners=[export.matrix_world@Vector(c) for c in export.bound_box]
bounds={"min":[min(p[i] for p in corners) for i in range(3)],"max":[max(p[i] for p in corners) for i in range(3)]}; dims=[bounds["max"][i]-bounds["min"][i] for i in range(3)]
failures=[]
if len(source_parts)<220: failures.append(f"insufficient parts {len(source_parts)}")
if len(collections)!=16 or any(len(c.objects)==0 for c in collections.values()): failures.append("sixteen-group hierarchy incomplete")
if dims[0]>7.2 or dims[1]>5.1 or dims[2]>9.7: failures.append(f"TBC visual envelope escaped {dims}")
if FBX_OUT.stat().st_size<250000: failures.append("FBX implausibly small")
manifest={"$schema":"cairnwell/source/press-module-prototype-v020/v1","created_utc":datetime.now(timezone.utc).isoformat(),"status":"SOURCE_ONLY_PRO_ALIGNED_S03_SIXTEEN_GROUP_PRESS__UNREAL_INTAKE_REQUIRED__NOT_PROMOTED","parent_blend":str(PARENT.relative_to(ROOT)).replace("\\","/"),"parent_sha256":PARENT_SHA,"visual_reference":{"external_path":str(REFERENCE).replace("\\","/"),"sha256":REFERENCE_SHA,"sheet_id":"CA-AMW-PT-A-S03-REF-01","dimensions":"ALL_TBC"},"asset_name":export.name,"assembly_groups":{name:len(collections[name].objects) for name in groups},"authored_part_count":len(source_parts),"added_pro_alignment_parts":len(added),"vertices":len(export.data.vertices),"polygons":len(export.data.polygons),"bounds_m":bounds,"dimensions_m":dims,"dimensions_authority":"TBC_VISUAL_PROPORTION_ONLY","collision_intent":"NoCollision","runtime_authority_added":False,"retained_assets_edited":False,"fbx":{"file":"FBX/"+FBX_OUT.name,"bytes":FBX_OUT.stat().st_size,"sha256":sha(FBX_OUT)},"renders":["Renders/"+v[0] for v in views]}
MANIFEST.write_text(json.dumps(manifest,indent=2),encoding="utf-8")
validation={"status":"PASS__PRO_ALIGNED_S03_SIXTEEN_GROUP_SOURCE__FRESH_VISUAL_AND_ISOLATED_UNREAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V020_SOURCE_NOT_RETAINED","assembly_group_count":len(collections),"assembly_group_counts":{name:len(collections[name].objects) for name in groups},"authored_part_count":len(source_parts),"added_pro_alignment_parts":len(added),"vertices":len(export.data.vertices),"polygons":len(export.data.polygons),"dimensions_m":dims,"retained_assets_edited":False,"promotion_authorized":False,"failures":failures}
VALIDATION.write_text(json.dumps(validation,indent=2),encoding="utf-8")
if failures: raise RuntimeError("; ".join(failures))
print(json.dumps(validation,indent=2))
