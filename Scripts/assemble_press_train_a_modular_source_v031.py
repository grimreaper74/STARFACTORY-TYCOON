"""Assemble complete modular Train A on retained v012 stage datums."""
import bpy,hashlib,json,math
from datetime import datetime,timezone
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
COMMON=ROOT/"SourceAssets/Candidate/PressTrains/Shared/PressBodyModuleLibrary_v025/FBX"
TOOLS=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/StationToolingVariants_v030/FBX"
ENDS=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/DedicatedEndCellsGuarded_v029/FBX"
OUT=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/ModularAssembly_v031";REVIEW=OUT/"Review";FBX=OUT/"FBX";BLEND=OUT/"CA_MW_PressTrainA_ModularAssembly_v031.blend";MANIFEST=OUT/"PRESS_TRAIN_A_MODULAR_ASSEMBLY_MANIFEST_v031.json";VALIDATION=OUT/"PRESS_TRAIN_A_MODULAR_ASSEMBLY_VALIDATION_v031.json"
for d in (OUT,REVIEW,FBX):d.mkdir(parents=True,exist_ok=True)
if any(p.exists() for p in (BLEND,MANIFEST,VALIDATION)) or any(REVIEW.glob("*.png")) or any(FBX.glob("*.fbx")):raise RuntimeError("refusing to overwrite v031")
DATUMS={"S01":0.0,"S02":7.5,"S03":15.0,"S04":22.5,"S05":30.0,"S06":37.5,"S07":45.0};VARIANTS={"S02":"DeepDraw","S03":"RestrikeForm","S04":"TrimScrap","S05":"PierceSlug","S06":"FlangeHem"}
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for c in iter(lambda:f.read(1048576),b""):h.update(c)
 return h.hexdigest().upper()
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;root=bpy.data.collections.new("CA_MW_PressTrainA_ModularAssembly_v031");scene.collection.children.link(root);stages={s:bpy.data.collections.new(f"TrainA_{s}_v031") for s in DATUMS}
for c in stages.values():root.children.link(c)
def import_to(path,stage,role):
 before=set(bpy.data.objects);bpy.ops.import_scene.fbx(filepath=str(path));new=[o for o in bpy.data.objects if o not in before]
 for o in new:
  for c in list(o.users_collection):c.objects.unlink(o)
  stages[stage].objects.link(o);o.location.y+=DATUMS[stage];o.name=f"PTA_{stage}_{role}_{o.name}_v031";o["train_id"]="A";o["station_id"]=stage;o["assembly_role"]=role;o["engineering_status"]="VISUAL_TBC";o["runtime_authority"]="NONE_SOURCE_ONLY";o["collision_intent"]="NoCollision_SOURCE_ONLY"
 return new
common_files=[p for p in sorted(COMMON.glob("*.fbx")) if "_07_BolsterTooling_" not in p.name]
if len(common_files)!=15:raise RuntimeError(f"expected 15 common modules, found {len(common_files)}")
records=[]
for s in ("S02","S03","S04","S05","S06"):
 for p in common_files:import_to(p,s,"Common_"+p.stem.split("PressBody_")[-1].replace("_v025",""))
 tp=TOOLS/f"SM_CA_MW_PTA_{s}_Tooling_v030.fbx";import_to(tp,s,"Tooling_"+VARIANTS[s]);records.append({"station":s,"datum_y_m_inherited_v012":DATUMS[s],"variant":VARIANTS[s],"common_modules":15,"tooling_fbx":str(tp.relative_to(ROOT)).replace("\\","/"),"tooling_sha256":sha(tp)})
for s,token in (("S01","S01_DestackBlankFeed"),("S07","S07_InspectionUnload")):
 p=next(ENDS.glob(f"*{token}*.fbx"));import_to(p,s,"DedicatedCell");records.append({"station":s,"datum_y_m_inherited_v012":DATUMS[s],"variant":token,"dedicated_fbx":str(p.relative_to(ROOT)).replace("\\","/"),"dedicated_sha256":sha(p)})
def mat(name,color,metal=.0,rough=.45):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;bs=m.node_tree.nodes.get("Principled BSDF");bs.inputs["Base Color"].default_value=(*color,1);bs.inputs["Metallic"].default_value=metal;bs.inputs["Roughness"].default_value=rough;return m
STEEL=mat("CA_MW_v031_TransferSteel",(.15,.18,.20),.75,.25);GREEN=mat("CA_MW_v031_CairnwellGreen",(.025,.20,.13),.35,.32);WHITE=mat("CA_MW_v031_Label",(.82,.86,.82),.05,.35)
def box(n,p,d,m,c=root):
 bpy.ops.mesh.primitive_cube_add(location=p);o=bpy.context.object;o.name=n;o.dimensions=d;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 for old in list(o.users_collection):old.objects.unlink(o)
 c.objects.link(o);o["engineering_status"]="VISUAL_TBC_OR_INHERITED_V012_DATUM";o["runtime_authority"]="NONE_SOURCE_ONLY";return o
# Retained v012 transfer route and visually small station identities.
for x in (-1.45,1.45):box(f"PTA_CommonTransferRail_{x:+.2f}_v031",(x,21.5,.47),(.14,48.0,.16),STEEL)
for s,y in DATUMS.items():
 box(f"PTA_{s}_IdentityPlate_v031",(-4.35,y,3.25),(.12,2.0,.58),GREEN,stages[s]);bpy.ops.object.text_add(location=(-4.43,y,3.25),rotation=(math.pi/2,0,-math.pi/2));t=bpy.context.object;t.name=f"PTA_{s}_IdentityText_v031";t.data.body=f"{s}  {VARIANTS.get(s, 'DESTACK / FEED' if s=='S01' else 'INSPECT / UNLOAD')}";t.data.align_x="CENTER";t.data.align_y="CENTER";t.data.size=.22;t.data.extrude=.008;t.data.materials.append(WHITE)
 for old in list(t.users_collection):old.objects.unlink(t)
 stages[s].objects.link(t);t["engineering_status"]="VISUAL_IDENTITY_ONLY"
def bounds(os):
 pts=[o.matrix_world@Vector(p) for o in os if o.type in {"MESH","CURVE","FONT"} for p in o.bound_box];return Vector(tuple(min(p[i] for p in pts) for i in range(3))),Vector(tuple(max(p[i] for p in pts) for i in range(3)))
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND),check_existing=False)
# Full assembly export.
all_geo=[o for o in bpy.data.objects if o.type in {"MESH","CURVE","FONT"}];bpy.ops.object.select_all(action="DESELECT")
for o in all_geo:o.select_set(True)
bpy.context.view_layer.objects.active=next(o for o in all_geo if o.type=="MESH");bpy.ops.object.duplicate()
for o in list(bpy.context.selected_objects):
 if o.type in {"CURVE","FONT"}:bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target="MESH")
bpy.ops.object.join();combined=bpy.context.object;combined.name="SM_CA_MW_PressTrainA_ModularAssembly_v031";combined.hide_render=True;lo,hi=bounds([combined]);assembly_fbx=FBX/f"{combined.name}.fbx";bpy.ops.object.select_all(action="DESELECT");combined.select_set(True);bpy.context.view_layer.objects.active=combined;bpy.ops.export_scene.fbx(filepath=str(assembly_fbx),use_selection=True,apply_unit_scale=True,apply_scale_options="FBX_SCALE_ALL",axis_forward="-Y",axis_up="Z",use_mesh_modifiers=True,mesh_smooth_type="FACE",add_leaf_bones=False,use_custom_props=True,object_types={"MESH"});combined.hide_render=True
# Neutral full-train review.
world=bpy.data.worlds.new("TrainAReviewWorld_v031");scene.world=world;world.use_nodes=True;world.node_tree.nodes["Background"].inputs["Color"].default_value=(.035,.045,.055,1);world.node_tree.nodes["Background"].inputs["Strength"].default_value=.42
for loc,e,size in (((35,-5,25),8000,18),((-30,48,18),6000,18),((10,24,28),5000,20)):bpy.ops.object.light_add(type="AREA",location=loc);l=bpy.context.object;l.data.energy=e;l.data.size=size
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type="ORTHO";cam.data.ortho_scale=56;scene.render.engine="BLENDER_EEVEE";scene.render.resolution_x=1800;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format="PNG"
def look(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat("-Z","Y").to_euler()
views=(("operator_elevation",(70,22.5,6),(0,22.5,4.4),56),("rear_service_elevation",(-70,22.5,6),(0,22.5,4.4),56),("elevated_operator",(55,-16,34),(0,22.5,3.2),63),("top_plan",(0,22.5,90),(0,22.5,0),58))
renders=[]
for name,loc,target,scale in views:cam.location=loc;cam.data.ortho_scale=scale;look(cam,target);path=REVIEW/f"train_a_{name}_v031.png";scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);renders.append({"view":name,"file":"Review/"+path.name,"sha256":sha(path)})
fail=[];dims=list(hi-lo)
if len(records)!=7:fail.append("seven stations required")
if any(abs(DATUMS[f"S0{i}"]-(i-1)*7.5)>.0001 for i in range(1,8)):fail.append("v012 datum inheritance mismatch")
if assembly_fbx.stat().st_size<1000000:fail.append("assembly export implausibly small")
manifest={"$schema":"cairnwell/source/press-train-a-modular-assembly-v031/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"SOURCE_ONLY_COMPLETE_SEVEN_STATION_MODULAR_ASSEMBLY__FRESH_VISUAL_DECISION_REQUIRED__NOT_PROMOTED" if not fail else "FAIL__NOT_RETAINED","datum_authority":{"source":"AssemblyStudy_v012 manifest","stage_centres_y_m":DATUMS,"engineering_status":"INHERITED_CURRENT_GAME_DATUMS__ALL_REAL_INSTALLATION_VALUES_TBC"},"station_records":records,"common_press_body":{"library":"PressBodyModuleLibrary_v025","module_count_per_press":15,"stations":["S02","S03","S04","S05","S06"]},"assembly":{"objects_before_join":len(all_geo),"vertices":len(combined.data.vertices),"polygons":len(combined.data.polygons),"bounds_m_tbc":[list(lo),list(hi)],"dimensions_m_tbc":dims,"fbx":"FBX/"+assembly_fbx.name,"bytes":assembly_fbx.stat().st_size,"sha256":sha(assembly_fbx)},"renders":renders,"engineering_values":"TBC_NOT_INVENTED","runtime_authority_added":False,"retained_assets_edited":False,"promotion_authorized":False};MANIFEST.write_text(json.dumps(manifest,indent=2),encoding="utf-8");validation={"status":manifest["status"],"station_count":len(records),"shared_press_station_count":5,"unique_tooling_variant_count":len(VARIANTS),"fresh_render_count":len(renders),"failures":fail,"promotion_authorized":False};VALIDATION.write_text(json.dumps(validation,indent=2),encoding="utf-8")
if fail:raise RuntimeError("; ".join(fail))
print(json.dumps(validation,indent=2))
