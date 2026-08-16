"""Refine failed v028 into locally guarded, mechanism-first S01/S07 cells."""
import bpy, hashlib, json
from datetime import datetime,timezone
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/DedicatedEndCellsOpen_v028/CA_MW_PressTrainA_DedicatedEndCellsOpen_v028.blend"; SRC_SHA="00E7233AF7FD71958CF2CF01DF901D8D2690CC5D9B73776F4508FDC08FAC0463"
OUT=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/DedicatedEndCellsGuarded_v029"; FBX=OUT/"FBX"; REVIEW=OUT/"FullCellReview"; ROUNDTRIP=OUT/"RoundTrip"
BLEND=OUT/"CA_MW_PressTrainA_DedicatedEndCellsGuarded_v029.blend"; MANIFEST=OUT/"DEDICATED_END_CELLS_GUARDED_MANIFEST_v029.json"; VALIDATION=OUT/"DEDICATED_END_CELLS_GUARDED_VALIDATION_v029.json"
for d in (OUT,FBX,REVIEW,ROUNDTRIP): d.mkdir(parents=True,exist_ok=True)
if any(p.exists() for p in (BLEND,MANIFEST,VALIDATION)) or any(FBX.glob("*.fbx")): raise RuntimeError("refusing to overwrite v029")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for c in iter(lambda:f.read(1048576),b""): h.update(c)
 return h.hexdigest().upper()
if sha(SRC)!=SRC_SHA: raise RuntimeError("v028 hash drift")
bpy.ops.wm.open_mainfile(filepath=str(SRC)); scene=bpy.context.scene; root=bpy.data.collections.get("CA_MW_PressTrainA_DedicatedEndCellsOpen_v028")
cells={"S01_DestackBlankFeed":next(c for c in root.children if c.name.startswith("S01_")),"S07_InspectionUnload":next(c for c in root.children if c.name.startswith("S07_"))}
for o in list(bpy.data.objects):
 if o.type in {"LIGHT","CAMERA"} or o.name.startswith("SM_CA_MW_") or any(t in o.name for t in ("OpenPost","BackHeader","SideHeader","SideRail","BackRail","Nameplate")): bpy.data.objects.remove(o,do_unlink=True)
def mat(t,f=None): return next((m for m in bpy.data.materials if t.lower() in m.name.lower()),None) or f or bpy.data.materials[0]
Y=mat("yellow"); D=mat("dark"); G=mat("green")
def objs(c): return [o for o in c.objects if o.type in {"MESH","CURVE","FONT"} and not o.name.startswith("SM_CA_MW_")]
def bounds(os):
 pts=[o.matrix_world@Vector(p) for o in os for p in o.bound_box]; return Vector(tuple(min(p[i] for p in pts) for i in range(3))),Vector(tuple(max(p[i] for p in pts) for i in range(3)))
added=[]
def box(n,p,d,m,c):
 bpy.ops.mesh.primitive_cube_add(location=p); o=bpy.context.object; o.name=n; o.dimensions=d; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(m)
 for old in list(o.users_collection): old.objects.unlink(o)
 c.objects.link(o); o["engineering_status"]="VISUAL_TBC"; o["runtime_authority"]="NONE_SOURCE_ONLY"; o["collision_intent"]="NoCollision_SOURCE_ONLY"; added.append(o); return o
def guard_panel(n,c,x,y,length,axis):
 h=1.75; post=.075
 if axis=="X":
  for px in (x-length/2,x+length/2): box(n+f"_Post_{px:.2f}_v029",(px,y,h/2),(post,post,h),Y,c)
  for z in (.15,h): box(n+f"_Rail_{z:.2f}_v029",(x,y,z),(length,post,post),Y,c)
  for i in range(1,9): box(n+f"_WireV_{i:02d}_v029",(x-length/2+i*length/9,y,h*.53),(.018,.028,h*.76),D,c)
  for i in range(1,5): box(n+f"_WireH_{i:02d}_v029",(x,y,i*h/5),(length-.10,.028,.018),D,c)
 else:
  for py in (y-length/2,y+length/2): box(n+f"_Post_{py:.2f}_v029",(x,py,h/2),(post,post,h),Y,c)
  for z in (.15,h): box(n+f"_Rail_{z:.2f}_v029",(x,y,z),(post,length,post),Y,c)
  for i in range(1,9): box(n+f"_WireV_{i:02d}_v029",(x,y-length/2+i*length/9,h*.53),(.028,.018,h*.76),D,c)
  for i in range(1,5): box(n+f"_WireH_{i:02d}_v029",(x,y,i*h/5),(.028,length-.10,.018),D,c)
for key,c in cells.items():
 c.name=c.name.replace("v028","v029"); lo,hi=bounds(objs(c)); x0,x1=lo.x-.22,hi.x+.22; y1=hi.y+.22
 guard_panel(key+"_RearGuard",c,(x0+x1)/2,y1,x1-x0,"X")
 guard_panel(key+"_LeftGuard",c,x0,(lo.y+y1)/2,y1-lo.y,"Y")
 # Compact identity on rear guard and amber gate posts at the open operator side.
 box(key+"_IdentityPlate_v029",((x0+x1)/2,y1+.045,1.42),(min(1.9,(x1-x0)*.38),.055,.34),G,c)
 for x in (x0,x1): box(key+f"_GatePost_{x:.2f}_v029",(x,lo.y-.05,.9),(.10,.10,1.8),Y,c)
 # Add visible fasteners/sensor blocks to lift-table or inspection portal without changing function.
 for i in range(6): box(key+f"_SensorBlock_{i:02d}_v029",(lo.x+.45+i*.32,lo.y+.08,1.10+(i%2)*.18),(.12,.10,.10),D,c)
 for o in objs(c): o.name=o.name.replace("v028","v029")
exports=[]
for key,c in cells.items():
 source=objs(c); bpy.ops.object.select_all(action="DESELECT")
 for o in source:o.select_set(True)
 bpy.context.view_layer.objects.active=source[0]; bpy.ops.object.duplicate()
 for o in list(bpy.context.selected_objects):
  if o.type in {"CURVE","FONT"}: bpy.context.view_layer.objects.active=o; bpy.ops.object.convert(target="MESH")
 bpy.ops.object.join(); out=bpy.context.object; out.name=f"SM_CA_MW_PTA_{key}_Guarded_v029"; out.hide_render=True; lo,hi=bounds([out]); path=FBX/f"{out.name}.fbx"
 bpy.ops.object.select_all(action="DESELECT"); out.select_set(True); bpy.context.view_layer.objects.active=out; bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,apply_unit_scale=True,apply_scale_options="FBX_SCALE_ALL",axis_forward="-Y",axis_up="Z",use_mesh_modifiers=True,mesh_smooth_type="FACE",add_leaf_bones=False,use_custom_props=True,object_types={"MESH"})
 exports.append({"cell":key,"parts":len(source),"vertices":len(out.data.vertices),"polygons":len(out.data.polygons),"dimensions_m_tbc":list(hi-lo),"fbx":str(path.relative_to(ROOT)).replace("\\","/"),"bytes":path.stat().st_size,"sha256":sha(path)}); bpy.data.objects.remove(out,do_unlink=True)
# Preserve the separately authored source before any clean-scene validation.
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND),check_existing=False)
# Independent clean-scene FBX round-trip counts and bounds.
roundtrips=[]
for record in exports:
 bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=str(ROOT/record["fbx"])); meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]; lo,hi=bounds(meshes)
 roundtrips.append({"cell":record["cell"],"mesh_count":len(meshes),"vertices":sum(len(o.data.vertices) for o in meshes),"polygons":sum(len(o.data.polygons) for o in meshes),"dimensions_m":list(hi-lo)})
# Import the exported cells into a new empty scene for deterministic review.
bpy.ops.wm.read_factory_settings(use_empty=True); scene=bpy.context.scene; review_cells={}
for record in exports:
 bpy.ops.import_scene.fbx(filepath=str(ROOT/record["fbx"])); imported=[o for o in scene.objects if o.type=="MESH" and o not in sum(review_cells.values(),[])]; review_cells[record["cell"]]=imported
world=bpy.data.worlds.new("GuardedCellsWorld_v029"); scene.world=world; world.use_nodes=True; world.node_tree.nodes["Background"].inputs["Color"].default_value=(.06,.075,.09,1); world.node_tree.nodes["Background"].inputs["Strength"].default_value=.55
for loc,e,s in (((5,-8,10),2200,7),((-6,-3,7),1500,6),((1,7,8),1700,6)): bpy.ops.object.light_add(type="AREA",location=loc); l=bpy.context.object; l.data.energy=e; l.data.shape="DISK"; l.data.size=s
bpy.ops.object.camera_add(); cam=bpy.context.object; cam.data.lens=52; scene.camera=cam; scene.render.engine="BLENDER_EEVEE"; scene.render.resolution_x=1600; scene.render.resolution_y=1000; scene.render.resolution_percentage=100; scene.render.image_settings.file_format="PNG"
def look(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat("-Z","Y").to_euler()
renders=[]
for key,os in review_cells.items():
 for k,other in review_cells.items():
  for o in other:o.hide_render=k!=key
 lo,hi=bounds(os); centre=(lo+hi)/2; span=max(hi-lo)
 for view,d in (("operator",Vector((1.3,-1.75,.7))),("front",Vector((0,-1.95,.28))),("elevated",Vector((1.4,-1.55,1.18)))):
  cam.location=centre+d.normalized()*span*1.75; look(cam,centre); path=REVIEW/f"{key[:3].lower()}_{view}_guarded_v029.png"; scene.render.filepath=str(path); bpy.ops.render.render(write_still=True); renders.append({"cell":key,"view":view,"file":str(path.relative_to(ROOT)).replace("\\","/"),"sha256":sha(path)})
fail=[]
for a,b in zip(exports,roundtrips):
 if b["mesh_count"]<1 or b["vertices"]!=a["vertices"] or b["polygons"]!=a["polygons"]: fail.append(a["cell"]+" round-trip geometry mismatch")
 if max(abs(b["dimensions_m"][i]-a["dimensions_m_tbc"][i]) for i in range(3))>.003: fail.append(a["cell"]+" round-trip dimension drift")
manifest={"$schema":"cairnwell/source/press-train-a-dedicated-end-cells-guarded-v029/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"SOURCE_AND_FBX_ROUNDTRIP_PASS__VISUAL_REVIEW_REQUIRED__NOT_PROMOTED" if not fail else "FAIL__NOT_RETAINED","source_parent":{"path":str(SRC.relative_to(ROOT)).replace("\\","/"),"sha256":SRC_SHA,"status":"FAILED_V028_DIRECTION_ONLY"},"exports":exports,"roundtrip":roundtrips,"renders":renders,"added_guard_detail_parts":len(added),"engineering_values":"TBC_NOT_INVENTED","runtime_authority_added":False,"retained_assets_edited":False,"promotion_authorized":False}; MANIFEST.write_text(json.dumps(manifest,indent=2),encoding="utf-8")
validation={"status":manifest["status"],"exports":len(exports),"fresh_renders":len(renders),"failures":fail,"retained_assets_edited":False,"promotion_authorized":False}; VALIDATION.write_text(json.dumps(validation,indent=2),encoding="utf-8")
if fail: raise RuntimeError("; ".join(fail))
print(json.dumps(validation,indent=2))
