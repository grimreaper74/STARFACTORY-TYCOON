"""Extract and refine dedicated S01/S07 cells from retained AssemblyStudy v012."""
import bpy, hashlib, json, math
from datetime import datetime, timezone
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/AssemblyStudy_v012/CA_MW_PressTrainA_AssemblyStudy_v012.blend"
SOURCE_SHA="B09BD2ABEC29FCD6D0BA215CDDE6B6E451D935D36C9BD397835F04AD1E50980F"
REF_SHA="4638AAD84029DFAD74941CCD0586B182E4F39D4EE6230E3D87B388BF87E95DFD"
OUT=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/DedicatedEndCells_v026"; FBX_DIR=OUT/"FBX"; REVIEW=OUT/"Renders"
BLEND=OUT/"CA_MW_PressTrainA_DedicatedEndCells_v026.blend"; MANIFEST=OUT/"DEDICATED_END_CELLS_MANIFEST_v026.json"; VALIDATION=OUT/"DEDICATED_END_CELLS_VALIDATION_v026.json"
for d in (OUT,FBX_DIR,REVIEW): d.mkdir(parents=True,exist_ok=True)
if any(p.exists() for p in (BLEND,MANIFEST,VALIDATION)) or any(FBX_DIR.glob("*.fbx")): raise RuntimeError("refusing to overwrite v026")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1048576),b""): h.update(c)
    return h.hexdigest().upper()
if sha(SOURCE)!=SOURCE_SHA: raise RuntimeError("AssemblyStudy v012 hash drift")
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene=bpy.context.scene
source_objects=list(bpy.data.objects)
new_root=bpy.data.collections.new("CA_MW_PressTrainA_DedicatedEndCells_v026"); scene.collection.children.link(new_root)
collections={k:bpy.data.collections.new(k+"_v026") for k in ("S01_DestackBlankFeed","S07_InspectionUnload")}
for c in collections.values(): new_root.children.link(c)
cells={"S01_DestackBlankFeed":[],"S07_InspectionUnload":[]}
for key,prefix in (("S01_DestackBlankFeed","PTA_S01_"),("S07_InspectionUnload","PTA_S07_")):
    for src in source_objects:
        if not src.name.startswith(prefix): continue
        o=src.copy();
        if src.data: o.data=src.data.copy()
        o.animation_data_clear(); o.name=src.name+"_v026"; collections[key].objects.link(o); cells[key].append(o)
        o["station_family"]=key; o["engineering_status"]="VISUAL_TBC"; o["collision_intent"]="NoCollision_SOURCE_ONLY"; o["runtime_authority"]="NONE_SOURCE_ONLY"
if len(cells["S01_DestackBlankFeed"])<35 or len(cells["S07_InspectionUnload"])<45: raise RuntimeError("end-cell extraction incomplete")
for o in source_objects: bpy.data.objects.remove(o,do_unlink=True)
for c in list(scene.collection.children):
    if c!=new_root: scene.collection.children.unlink(c)
def bounds(objects):
    pts=[o.matrix_world@Vector(c) for o in objects if o.type in {"MESH","CURVE","FONT"} for c in o.bound_box]
    return [min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]
normalization={}
for key,objects in cells.items():
    lo,hi=bounds(objects); shift=Vector((-(lo[0]+hi[0])/2,-(lo[1]+hi[1])/2,-lo[2]))
    for o in objects: o.location+=shift
    lo2,hi2=bounds(objects); normalization[key]={"source_bounds_mm_visual":[lo,hi],"local_shift_m":list(shift),"local_dimensions_m_tbc":[hi2[i]-lo2[i] for i in range(3)]}
def mat(token,fall=None):
    m=next((x for x in bpy.data.materials if token.lower() in x.name.lower()),None)
    return m or fall or bpy.data.materials[0]
GREEN=mat("green"); DARK=mat("dark"); STEEL=mat("steel",DARK); YELLOW=mat("yellow",GREEN); GRAPHITE=mat("graphite",DARK)
added=[]
def box(n,p,d,m,key,b=.025):
    bpy.ops.mesh.primitive_cube_add(location=p); o=bpy.context.object; o.name=n; o.dimensions=d; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(m)
    for c in list(o.users_collection): c.objects.unlink(o)
    collections[key].objects.link(o); o["station_family"]=key; o["engineering_status"]="VISUAL_TBC"; o["collision_intent"]="NoCollision_SOURCE_ONLY"; o["runtime_authority"]="NONE_SOURCE_ONLY"
    if b:
        md=o.modifiers.new("FabricatedEdge","BEVEL"); md.width=min(b,min(d)*.18); md.segments=2
    cells[key].append(o); added.append(o); return o
def cyl(n,p,r,depth,m,key,rot=(0,0,0),verts=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=p,rotation=rot); o=bpy.context.object; o.name=n; o.data.materials.append(m)
    for c in list(o.users_collection): c.objects.unlink(o)
    collections[key].objects.link(o); o["station_family"]=key; o["engineering_status"]="VISUAL_TBC"; o["collision_intent"]="NoCollision_SOURCE_ONLY"; o["runtime_authority"]="NONE_SOURCE_ONLY"; cells[key].append(o); added.append(o); return o

# Reference-led missing unique modules. Positions are visual/TBC within local cells.
s1="S01_DestackBlankFeed"; s7="S07_InspectionUnload"
for x in (-1.35,-.45,.45,1.35):
    cyl(f"S01_SeparatorMagnet_{x:+.2f}_v026",(x,-.45,1.20),.075,.30,DARK,s1,(math.pi/2,0,0),20)
box("S01_FeedHandoffBed_v026",(2.45,0,.62),(2.30,1.55,.18),GRAPHITE,s1,.035)
for x in (1.55,1.95,2.35,2.75,3.15,3.55): cyl(f"S01_HandoffRoller_{x:.2f}_v026",(x,0,.76),.07,1.28,STEEL,s1,(math.pi/2,0,0),20)
box("S01_SensorArchHeader_v026",(2.70,0,2.10),(1.55,.16,.16),YELLOW,s1,.018)
for y in (-.66,.66): box(f"S01_SensorArchPost_{y:+.2f}_v026",(2.70,y,1.38),(.16,.16,1.60),YELLOW,s1,.018)

box("S07_AcceptedHoldDiverter_v026",(2.20,0,.72),(1.55,1.75,.22),GRAPHITE,s7,.035)
box("S07_AcceptedLane_v026",(3.35,-.54,.70),(1.10,.64,.16),GREEN,s7,.025)
box("S07_HoldLane_v026",(3.35,.54,.70),(1.10,.64,.16),YELLOW,s7,.025)
box("S07_OutputBufferFrame_v026",(4.50,-.54,.58),(1.35,.82,.18),GRAPHITE,s7,.035)
for x in (3.95,4.25,4.55,4.85,5.15): cyl(f"S07_OutputRoller_{x:.2f}_v026",(x,-.54,.72),.065,.66,STEEL,s7,(math.pi/2,0,0),20)
for x in (-.55,.55):
    box(f"S07_InspectionCameraPost_{x:+.2f}_v026",(x,0,2.05),(.10,.10,2.30),YELLOW,s7,.012)
    box(f"S07_InspectionCamera_{x:+.2f}_v026",(x,-.08,3.15),(.32,.24,.20),DARK,s7,.025)

records=[]
for key in (s1,s7):
    objects=[o for o in cells[key] if o.type in {"MESH","CURVE","FONT"}]
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects: o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]; bpy.ops.object.duplicate()
    for o in list(bpy.context.selected_objects):
        if o.type in {"CURVE","FONT"}: bpy.context.view_layer.objects.active=o; bpy.ops.object.convert(target="MESH")
    bpy.ops.object.join(); export=bpy.context.object; export.name="SM_CA_MW_PTA_"+key+"_v026"; export.hide_render=True
    export["engineering_status"]="VISUAL_TBC"; export["collision_intent"]="NoCollision_SOURCE_ONLY"; export["runtime_authority"]="NONE_SOURCE_ONLY"
    lo,hi=bounds([export]); dims=[hi[i]-lo[i] for i in range(3)]
    fbx=FBX_DIR/(export.name+".fbx"); bpy.ops.object.select_all(action="DESELECT"); export.select_set(True); bpy.context.view_layer.objects.active=export
    bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,apply_unit_scale=True,apply_scale_options="FBX_SCALE_ALL",axis_forward="-Y",axis_up="Z",use_mesh_modifiers=True,mesh_smooth_type="FACE",add_leaf_bones=False,use_custom_props=True,object_types={"MESH"})
    records.append({"cell":key,"source_part_count":len(objects),"vertices":len(export.data.vertices),"polygons":len(export.data.polygons),"dimensions_m_tbc":dims,"fbx":"FBX/"+fbx.name,"bytes":fbx.stat().st_size,"sha256":sha(fbx)})
    bpy.data.objects.remove(export,do_unlink=True)

# Neutral review stage and separate full-cell captures.
world=scene.world or bpy.data.worlds.new("DedicatedEndCellsWorld_v026"); scene.world=world; world.use_nodes=True; world.node_tree.nodes["Background"].inputs["Color"].default_value=(.025,.035,.045,1); world.node_tree.nodes["Background"].inputs["Strength"].default_value=.32
bpy.ops.object.light_add(type="AREA",location=(4,-7,9)); keylight=bpy.context.object; keylight.data.energy=1800; keylight.data.shape="DISK"; keylight.data.size=7
bpy.ops.object.light_add(type="AREA",location=(-6,4,6)); fill=bpy.context.object; fill.data.energy=1100; fill.data.size=6
bpy.ops.object.camera_add(); camera=bpy.context.object; camera.data.lens=58; scene.camera=camera
def look(o,t): o.rotation_euler=(Vector(t)-o.location).to_track_quat("-Z","Y").to_euler()
scene.render.engine="BLENDER_EEVEE_NEXT"; scene.render.resolution_x=1600; scene.render.resolution_y=1000; scene.render.resolution_percentage=100; scene.render.image_settings.file_format="PNG"
views=[]
for key,loc in ((s1,(10,-13,7)),(s7,(11,-14,7))):
    for k,objs in cells.items():
        for o in objs: o.hide_render=(k!=key)
    camera.location=loc; look(camera,(0,0,1.8)); fn=("01_s01_destack_feed_v026.png" if key==s1 else "02_s07_inspection_unload_v026.png"); scene.render.filepath=str(REVIEW/fn); bpy.ops.render.render(write_still=True); views.append("Renders/"+fn)
for objs in cells.values():
    for o in objs: o.hide_render=False
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND),check_existing=False)
fail=[]
if len(records)!=2: fail.append("expected two dedicated cells")
if records[0]["source_part_count"]<45: fail.append("S01 detail count too low")
if records[1]["source_part_count"]<65: fail.append("S07 detail count too low")
if any(x["bytes"]<100000 for x in records): fail.append("dedicated cell FBX implausibly small")
manifest={"$schema":"cairnwell/source/press-train-a-dedicated-end-cells-v026/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"SOURCE_ONLY_DEDICATED_S01_S07_CELLS__VISUAL_REVIEW_AND_UNREAL_INTAKE_REQUIRED__NOT_PROMOTED","source_parent":{"path":str(SOURCE.relative_to(ROOT)).replace('\\','/'),"sha256":SOURCE_SHA},"complete_train_reference_sha256":REF_SHA,"normalization":normalization,"cells":records,"added_reference_modules":len(added),"renders":views,"runtime_authority_added":False,"retained_assets_edited":False,"promotion_authorized":False}
MANIFEST.write_text(json.dumps(manifest,indent=2),encoding="utf-8")
validation={"status":"PASS_SOURCE_STRUCTURE__FRESH_VISUAL_DECISION_REQUIRED__NOT_PROMOTED" if not fail else "FAIL__V026_END_CELLS_NOT_RETAINED","cell_count":len(records),"cell_parts":{x["cell"]:x["source_part_count"] for x in records},"added_reference_modules":len(added),"retained_assets_edited":False,"promotion_authorized":False,"failures":fail}
VALIDATION.write_text(json.dumps(validation,indent=2),encoding="utf-8")
if fail: raise RuntimeError('; '.join(fail))
print(json.dumps(validation,indent=2))
