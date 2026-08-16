"""Non-overwriting, mechanism-first S01/S07 successor to rejected v027."""
import bpy, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/DedicatedEndCells_v027/CA_MW_PressTrainA_DedicatedEndCells_v027.blend"
SRC_SHA="FDD6B43C058BF679322E1C7FC7BBFCFED33008D34888B3E5D6226B32625F268F"
REF_SHA="4638AAD84029DFAD74941CCD0586B182E4F39D4EE6230E3D87B388BF87E95DFD"
OUT=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/DedicatedEndCellsOpen_v028"
FBX=OUT/"FBX"; REVIEW=OUT/"FullCellReview"
BLEND=OUT/"CA_MW_PressTrainA_DedicatedEndCellsOpen_v028.blend"
MANIFEST=OUT/"DEDICATED_END_CELLS_OPEN_MANIFEST_v028.json"
VALIDATION=OUT/"DEDICATED_END_CELLS_OPEN_VALIDATION_v028.json"
for d in (OUT,FBX,REVIEW): d.mkdir(parents=True,exist_ok=True)
if any(p.exists() for p in (BLEND,MANIFEST,VALIDATION)) or any(FBX.glob("*.fbx")) or any(REVIEW.glob("*.png")): raise RuntimeError("refusing to overwrite v028")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1048576),b""): h.update(c)
    return h.hexdigest().upper()
if sha(SRC)!=SRC_SHA: raise RuntimeError("v027 source hash drift")
bpy.ops.wm.open_mainfile(filepath=str(SRC)); scene=bpy.context.scene
root=bpy.data.collections.get("CA_MW_PressTrainA_DedicatedEndCells_v027")
if not root: raise RuntimeError("v027 root missing")
root.name="CA_MW_PressTrainA_DedicatedEndCellsOpen_v028"
cells={"S01_DestackBlankFeed":next(c for c in root.children if c.name.startswith("S01_")),"S07_InspectionUnload":next(c for c in root.children if c.name.startswith("S07_"))}
tokens=("OperatorFacade","GreenHeader","SiteIdentity","TrainABadge","_Identity","UtilityDrop","AccessGuard","EndRoof","EndColumn")
removed=[]
for o in list(bpy.data.objects):
    if o.name.startswith("SM_CA_MW_") or any(t in o.name for t in tokens): removed.append(o.name); bpy.data.objects.remove(o,do_unlink=True)
for o in list(bpy.data.objects):
    if o.type in {"LIGHT","CAMERA"}: bpy.data.objects.remove(o,do_unlink=True)
def mat(token,fallback=None): return next((m for m in bpy.data.materials if token.lower() in m.name.lower()),None) or fallback or bpy.data.materials[0]
YELLOW=mat("yellow"); GREEN=mat("green"); DARK=mat("dark")
def objects(c): return [o for o in c.objects if o.type in {"MESH","CURVE","FONT"} and not o.name.startswith("SM_CA_MW_")]
def bounds(objs):
    pts=[o.matrix_world@Vector(p) for o in objs for p in o.bound_box]
    return Vector(tuple(min(p[i] for p in pts) for i in range(3))),Vector(tuple(max(p[i] for p in pts) for i in range(3)))
added=[]
def box(n,p,d,m,c):
    bpy.ops.mesh.primitive_cube_add(location=p); o=bpy.context.object; o.name=n; o.dimensions=d; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(m)
    for old in list(o.users_collection): old.objects.unlink(o)
    c.objects.link(o); o["engineering_status"]="VISUAL_TBC"; o["collision_intent"]="NoCollision_SOURCE_ONLY"; o["runtime_authority"]="NONE_SOURCE_ONLY"
    be=o.modifiers.new("FabricatedEdge","BEVEL"); be.width=min(.014,min(d)*.17); be.segments=2; added.append(o); return o
frames={}
for key,c in cells.items():
    c.name=c.name.replace("_v027","_v028"); lo,hi=bounds(objects(c)); x0,x1=lo.x-.3,hi.x+.3; y0,y1=lo.y-.28,hi.y+.28; top=max(hi.z+.25,2.65); post=.10
    for i,(x,y) in enumerate(((x0,y0),(x1,y0),(x0,y1),(x1,y1)),1): box(f"{key}_OpenPost_{i:02d}_v028",(x,y,top/2),(post,post,top),YELLOW,c)
    box(f"{key}_BackHeader_v028",((x0+x1)/2,y1,top),(x1-x0+post,post,post),YELLOW,c)
    for side,x in (("L",x0),("R",x1)):
        box(f"{key}_SideHeader_{side}_v028",(x,(y0+y1)/2,top),(post,y1-y0,post),YELLOW,c)
        for z in (.55,1.1): box(f"{key}_SideRail_{side}_{int(z*100)}_v028",(x,(y0+y1)/2,z),(.065,y1-y0,.065),YELLOW,c)
    for z in (.55,1.1): box(f"{key}_BackRail_{int(z*100)}_v028",((x0+x1)/2,y1,z),(x1-x0,.065,.065),YELLOW,c)
    box(f"{key}_Nameplate_v028",((x0+x1)/2,y1+.05,min(top-.35,2.4)),(min(2.0,(x1-x0)*.42),.065,.38),GREEN,c)
    frames[key]={"mechanical_bounds_m_tbc":[list(lo),list(hi)],"open_frame_bounds_m_tbc":[[x0,y0,0],[x1,y1,top]]}
for c in cells.values():
    for o in objects(c): o.name=o.name.replace("_v027","_v028")
exports=[]
for key,c in cells.items():
    src=objects(c); bpy.ops.object.select_all(action="DESELECT")
    for o in src: o.select_set(True)
    bpy.context.view_layer.objects.active=src[0]; bpy.ops.object.duplicate()
    for o in list(bpy.context.selected_objects):
        if o.type in {"CURVE","FONT"}: bpy.context.view_layer.objects.active=o; bpy.ops.object.convert(target="MESH")
    bpy.ops.object.join(); out=bpy.context.object; out.name=f"SM_CA_MW_PTA_{key}_Open_v028"; out.hide_render=True; lo,hi=bounds([out]); path=FBX/f"{out.name}.fbx"
    bpy.ops.object.select_all(action="DESELECT"); out.select_set(True); bpy.context.view_layer.objects.active=out
    bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,apply_unit_scale=True,apply_scale_options="FBX_SCALE_ALL",axis_forward="-Y",axis_up="Z",use_mesh_modifiers=True,mesh_smooth_type="FACE",add_leaf_bones=False,use_custom_props=True,object_types={"MESH"})
    exports.append({"cell":key,"source_parts":len(src),"vertices":len(out.data.vertices),"polygons":len(out.data.polygons),"dimensions_m_tbc":list(hi-lo),"fbx":str(path.relative_to(ROOT)).replace("\\","/"),"bytes":path.stat().st_size,"sha256":sha(path)}); bpy.data.objects.remove(out,do_unlink=True)
world=scene.world or bpy.data.worlds.new("OpenCellsWorld_v028"); scene.world=world; world.use_nodes=True; world.node_tree.nodes["Background"].inputs["Color"].default_value=(.06,.075,.09,1); world.node_tree.nodes["Background"].inputs["Strength"].default_value=.55
for loc,energy,size in (((5,-8,10),2200,7),((-6,-3,7),1500,6),((1,7,8),1700,6)):
    bpy.ops.object.light_add(type="AREA",location=loc); l=bpy.context.object; l.data.energy=energy; l.data.shape="DISK"; l.data.size=size
bpy.ops.object.camera_add(); camera=bpy.context.object; camera.data.lens=52; scene.camera=camera; scene.render.engine="BLENDER_EEVEE"; scene.render.resolution_x=1600; scene.render.resolution_y=1000; scene.render.resolution_percentage=100; scene.render.image_settings.file_format="PNG"
def look(o,t): o.rotation_euler=(Vector(t)-o.location).to_track_quat("-Z","Y").to_euler()
renders=[]
for key,c in cells.items():
    for k,other in cells.items(): other.hide_render=k!=key
    lo,hi=bounds(objects(c)); centre=(lo+hi)/2; size=hi-lo; span=max(size)
    for view,direction in (("operator",Vector((1.3,-1.75,.7))),("front",Vector((0,-1.95,.28))),("elevated",Vector((1.4,-1.55,1.18)))):
        camera.location=centre+direction.normalized()*span*1.75; look(camera,centre); fn=f"{key[:3].lower()}_{view}_open_v028.png"; path=REVIEW/fn; scene.render.filepath=str(path); bpy.ops.render.render(write_still=True); renders.append({"cell":key,"view":view,"file":str(path.relative_to(ROOT)).replace("\\","/"),"sha256":sha(path)})
for c in cells.values(): c.hide_render=False
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND),check_existing=False)
fail=[]
if len(exports)!=2: fail.append("expected two exports")
if len(removed)<20: fail.append("facade removal count low")
if any(x["source_parts"]<45 or x["bytes"]<100000 for x in exports): fail.append("cell export incomplete")
manifest={"$schema":"cairnwell/source/press-train-a-dedicated-end-cells-open-v028/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"SOURCE_ONLY_OPEN_MECHANICAL_S01_S07__FRESH_VISUAL_DECISION_REQUIRED__NOT_PROMOTED","source_parent":{"path":str(SRC.relative_to(ROOT)).replace("\\","/"),"sha256":SRC_SHA,"visual_status":"REJECTED_V027"},"complete_train_reference_sha256":REF_SHA,"removed_presentation_shell_objects":removed,"frame_records":frames,"exports":exports,"renders":renders,"engineering_values":"TBC_NOT_INVENTED","runtime_authority_added":False,"retained_assets_edited":False,"promotion_authorized":False}; MANIFEST.write_text(json.dumps(manifest,indent=2),encoding="utf-8")
validation={"status":"PASS_SOURCE_STRUCTURE__FRESH_VISUAL_DECISION_REQUIRED__NOT_PROMOTED" if not fail else "FAIL__V028_NOT_RETAINED","cell_count":len(exports),"removed_shell_objects":len(removed),"added_open_frame_parts":len(added),"cell_parts":{x["cell"]:x["source_parts"] for x in exports},"fresh_renders":len(renders),"failures":fail,"retained_assets_edited":False,"promotion_authorized":False}; VALIDATION.write_text(json.dumps(validation,indent=2),encoding="utf-8")
if fail: raise RuntimeError("; ".join(fail))
print(json.dumps(validation,indent=2))
