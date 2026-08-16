"""Build five visually distinct, datum-compatible S02-S06 tooling variants."""
import bpy, hashlib, json, math
from datetime import datetime,timezone
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/PressModulePrototype_v022/CA_MW_PressModulePrototype_v022.blend"; SRC_SHA="9B3A72FB41B5C52C928B77E165898B15FD3370A357CCCF1CD791593989DE9A51"
OUT=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/StationToolingVariants_v030"; FBX=OUT/"FBX"; REVIEW=OUT/"Review"; BLEND=OUT/"CA_MW_PressTrainA_StationToolingVariants_v030.blend"; MANIFEST=OUT/"STATION_TOOLING_VARIANTS_MANIFEST_v030.json"; VALIDATION=OUT/"STATION_TOOLING_VARIANTS_VALIDATION_v030.json"
for d in (OUT,FBX,REVIEW):d.mkdir(parents=True,exist_ok=True)
if any(p.exists() for p in (BLEND,MANIFEST,VALIDATION)) or any(FBX.glob("*.fbx")):raise RuntimeError("refusing to overwrite v030")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for c in iter(lambda:f.read(1048576),b""):h.update(c)
 return h.hexdigest().upper()
if sha(SRC)!=SRC_SHA:raise RuntimeError("v022 hash drift")
bpy.ops.wm.open_mainfile(filepath=str(SRC)); scene=bpy.context.scene; original=list(bpy.data.objects); old=bpy.data.collections.get("07_BolsterTooling_v022")
root=bpy.data.collections.new("CA_MW_PressTrainA_StationToolingVariants_v030"); scene.collection.children.link(root); cols={s:bpy.data.collections.new(f"{s}_{n}_v030") for s,n in (("S02","DeepDraw"),("S03","RestrikeForm"),("S04","TrimScrap"),("S05","PierceSlug"),("S06","FlangeHem"))}
for c in cols.values():root.children.link(c)
# Preserve S03 exactly from the retained v022 tooling collection.
for src in old.objects:
 o=src.copy(); o.data=src.data.copy() if src.data else None; o.name=src.name.replace("v022","v030"); cols["S03"].objects.link(o)
for o in original:bpy.data.objects.remove(o,do_unlink=True)
for c in list(scene.collection.children):
 if c!=root:scene.collection.children.unlink(c)
def mat(t,f=None):return next((m for m in bpy.data.materials if t.lower() in m.name.lower()),None) or f or bpy.data.materials[0]
STEEL=mat("steel"); DARK=mat("dark"); GREEN=mat("green",DARK); YELLOW=mat("yellow",GREEN); MACH=mat("mach",STEEL)
def tag(o,s):o["station_id"]=s;o["tooling_variant"]={"S02":"DeepDraw","S03":"RestrikeForm","S04":"TrimScrap","S05":"PierceSlug","S06":"FlangeHem"}[s];o["engineering_status"]="VISUAL_TBC";o["runtime_authority"]="NONE_SOURCE_ONLY";o["collision_intent"]="NoCollision_SOURCE_ONLY"
for o in cols["S03"].objects:tag(o,"S03")
def link(o,s):
 for c in list(o.users_collection):c.objects.unlink(o)
 cols[s].objects.link(o);tag(o,s);return o
def box(n,p,d,m,s,b=.025):
 bpy.ops.mesh.primitive_cube_add(location=p);o=bpy.context.object;o.name=f"{s}_{n}_v030";o.dimensions=d;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);link(o,s)
 if b:md=o.modifiers.new("FabricatedEdge","BEVEL");md.width=min(b,min(d)*.18);md.segments=2
 return o
def cyl(n,p,r,d,m,s,rot=(0,0,0),verts=24):
 bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=p,rotation=rot);o=bpy.context.object;o.name=f"{s}_{n}_v030";o.data.materials.append(m);return link(o,s)
def common_shoes(s):
 box("BolsterBase",(0,0,1.05),(3.7,2.44,.52),DARK,s);box("MachinedBolster",(0,0,1.39),(3.42,2.20,.18),MACH,s);box("LowerShoe",(0,0,1.66),(2.82,1.82,.20),DARK,s);box("UpperShoe",(0,0,4.86),(2.82,1.82,.18),DARK,s)
 for x in (-1.2,-.6,0,.6,1.2):box(f"BolsterSlot_{x:+.1f}",(x,-1.12,1.50),(.065,.07,.04),DARK,s,.005)
 for x in (-1.15,-.75,-.35,.35,.75,1.15):box(f"Clamp_{x:+.2f}",(x,-1.30,2.50),(.18,.34,.12),YELLOW,s,.012);cyl(f"ClampBolt_{x:+.2f}",(x,-1.48,2.58),.035,.06,STEEL,s)
# S02 deep draw: large cavity, blankholder and adjusters.
common_shoes("S02");box("DeepDrawLower",(0,0,2.18),(2.88,2.10,.46),GREEN,"S02");box("DeepDrawUpper",(0,0,4.30),(2.76,2.04,.40),GREEN,"S02")
for x,y in ((-1.05,-.70),(1.05,-.70),(-1.05,.70),(1.05,.70)):cyl(f"Blankholder_{x:+.2f}_{y:+.2f}",(x,y,2.47),.16,.24,MACH,"S02");cyl(f"Adjuster_{x:+.2f}_{y:+.2f}",(x,y,4.04),.10,.30,STEEL,"S02")
for x in (-.75,0,.75):box(f"DrawRib_{x:+.2f}",(x,0,2.47),(.18,1.40,.12),MACH,"S02",.01)
# S04 trim perimeter, four scrap chutes and two bins.
common_shoes("S04");box("TrimLower",(0,0,2.18),(2.82,2.02,.40),GREEN,"S04");box("TrimUpper",(0,0,4.30),(2.72,1.96,.34),GREEN,"S04")
for x,y,dx,dy in ((0,-.88,2.5,.10),(0,.88,2.5,.10),(-1.23,0,.10,1.65),(1.23,0,.10,1.65)):box(f"TrimKnife_{x:+.2f}_{y:+.2f}",(x,y,2.43),(dx,dy,.13),MACH,"S04",.008)
for x in (-1.65,1.65):box(f"ScrapChute_{x:+.2f}",(x,.60,1.60),(.52,1.12,.18),YELLOW,"S04");box(f"ScrapBin_{x:+.2f}",(x,1.45,.72),(.78,.72,.62),DARK,"S04")
# S05 pierce plate, punch array and slug conveyors/bins.
common_shoes("S05");box("PierceLower",(0,0,2.18),(2.82,2.02,.42),GREEN,"S05");box("PierceUpper",(0,0,4.30),(2.72,1.96,.34),GREEN,"S05")
for ix,x in enumerate((-1.0,-.5,0,.5,1.0)):
 for iy,y in enumerate((-.62,0,.62)):cyl(f"Punch_{ix}_{iy}",(x,y,4.04),.065,.30,MACH,"S05");cyl(f"SlugPort_{ix}_{iy}",(x,y,2.45),.09,.12,DARK,"S05")
for x in (-1.65,1.65):box(f"SlugConveyor_{x:+.2f}",(x,.55,1.48),(.42,1.20,.16),YELLOW,"S05");box(f"SlugBin_{x:+.2f}",(x,1.48,.65),(.70,.68,.58),DARK,"S05")
# S06 flange/hem rails, folding supports and final restrike pads.
common_shoes("S06");box("HemLower",(0,0,2.18),(2.86,2.06,.44),GREEN,"S06");box("HemUpper",(0,0,4.30),(2.74,1.98,.36),GREEN,"S06")
for y in (-.72,.72):box(f"FoldingRail_{y:+.2f}",(0,y,2.48),(2.50,.18,.20),MACH,"S06",.012)
for x in (-1.0,-.5,0,.5,1.0):box(f"HemSupport_{x:+.2f}",(x,0,2.52),(.14,1.25,.26),YELLOW,"S06",.01)
for x,y in ((-.9,-.62),(.9,-.62),(-.9,.62),(.9,.62)):box(f"RestrikePad_{x:+.2f}_{y:+.2f}",(x,y,4.04),(.30,.30,.24),MACH,"S06",.015)
def bounds(os):
 pts=[o.matrix_world@Vector(p) for o in os for p in o.bound_box];return Vector(tuple(min(p[i] for p in pts) for i in range(3))),Vector(tuple(max(p[i] for p in pts) for i in range(3)))
exports=[]
for s,c in cols.items():
 os=[o for o in c.objects if o.type in {"MESH","CURVE","FONT"}];bpy.ops.object.select_all(action="DESELECT")
 for o in os:o.select_set(True)
 bpy.context.view_layer.objects.active=os[0];bpy.ops.object.duplicate();bpy.ops.object.join();out=bpy.context.object;out.name=f"SM_CA_MW_PTA_{s}_Tooling_v030";out.hide_render=True;lo,hi=bounds([out]);path=FBX/f"{out.name}.fbx";bpy.ops.object.select_all(action="DESELECT");out.select_set(True);bpy.context.view_layer.objects.active=out;bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,apply_unit_scale=True,apply_scale_options="FBX_SCALE_ALL",axis_forward="-Y",axis_up="Z",use_mesh_modifiers=True,mesh_smooth_type="FACE",add_leaf_bones=False,use_custom_props=True,object_types={"MESH"});exports.append({"station":s,"variant":out["tooling_variant"] if "tooling_variant" in out else {"S02":"DeepDraw","S03":"RestrikeForm","S04":"TrimScrap","S05":"PierceSlug","S06":"FlangeHem"}[s],"parts":len(os),"vertices":len(out.data.vertices),"polygons":len(out.data.polygons),"dimensions_m_tbc":list(hi-lo),"fbx":"FBX/"+path.name,"bytes":path.stat().st_size,"sha256":sha(path)});bpy.data.objects.remove(out,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND),check_existing=False)
# Review each variant in the same camera/light setup.
world=scene.world or bpy.data.worlds.new("ToolingVariantsWorld_v030");scene.world=world;world.use_nodes=True;world.node_tree.nodes["Background"].inputs["Color"].default_value=(.05,.065,.08,1);world.node_tree.nodes["Background"].inputs["Strength"].default_value=.55
for loc,e,size in (((5,-7,8),1700,6),((-5,2,6),1100,5)):bpy.ops.object.light_add(type="AREA",location=loc);l=bpy.context.object;l.data.energy=e;l.data.size=size
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.lens=58;scene.camera=cam;scene.render.engine="BLENDER_EEVEE";scene.render.resolution_x=1400;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.image_settings.file_format="PNG"
def look(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat("-Z","Y").to_euler()
renders=[]
for s,c in cols.items():
 for k,other in cols.items():other.hide_render=k!=s
 cam.location=(6,-8,6);look(cam,(0,0,2.8));path=REVIEW/f"{s.lower()}_{dict((x['station'],x['variant']) for x in exports)[s].lower()}_v030.png";scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);renders.append({"station":s,"file":"Review/"+path.name,"sha256":sha(path)})
for c in cols.values():c.hide_render=False
fail=[]
if len(exports)!=5 or len({x["variant"] for x in exports})!=5:fail.append("five unique variants required")
if any(x["parts"]<25 for x in exports):fail.append("variant detail count low")
manifest={"$schema":"cairnwell/source/press-train-a-station-tooling-variants-v030/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"SOURCE_ONLY_FIVE_UNIQUE_TOOLING_VARIANTS__ASSEMBLY_AND_UNREAL_GATES_REQUIRED__NOT_PROMOTED" if not fail else "FAIL__NOT_RETAINED","source_parent":{"path":str(SRC.relative_to(ROOT)).replace("\\","/"),"sha256":SRC_SHA},"shared_body_contract":"Use with v025 common modules at preserved v022 station datum; never duplicate S03 tooling across S02/S04/S05/S06.","exports":exports,"renders":renders,"engineering_values":"ALL_DIMENSIONS_AND_INTERFACES_TBC","runtime_authority_added":False,"retained_assets_edited":False,"promotion_authorized":False};MANIFEST.write_text(json.dumps(manifest,indent=2),encoding="utf-8");validation={"status":manifest["status"],"variant_count":len(exports),"variants":{x["station"]:x["variant"] for x in exports},"failures":fail,"promotion_authorized":False};VALIDATION.write_text(json.dumps(validation,indent=2),encoding="utf-8")
if fail:raise RuntimeError("; ".join(fail))
print(json.dumps(validation,indent=2))
