"""Stage unique P0/P1 support meshes and instance transforms from v660."""
import bpy,hashlib,json,re,math
from pathlib import Path
from datetime import datetime,timezone
from mathutils import Matrix,Vector
ROOT=Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE=ROOT/r"SourceAssets\Candidate\PressTrains\TrainA\CompleteTrainAAssembly_v660\CA_MW_PressTrainA_CompleteAssembly_v660.blend"
OUT=ROOT/r"Saved\ImportStaging\CompleteTrainASupports_v661";OUT.mkdir(parents=True,exist_ok=True)
AUDIT=ROOT/r"Saved\Audits\PressTrains\complete_train_a_support_staging_v661.json"
if AUDIT.exists():raise RuntimeError("Refusing to overwrite v661")
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
tokens=("_TR_Transfer_","DestackBlankFeed","TrimScrap_v640","SlugCollection_v640","InspectUnload_v640",
 "DieCart_v660","_HPU_","LargeTrimBin","SmallSlugBin","FlatPanelStillage","PoweredConveyor")
objects=[o for o in bpy.context.scene.objects if o.type=="MESH" and any(t in o.name for t in tokens)]
if len(objects)!=19:raise RuntimeError(f"Expected 19 support instances, got {len(objects)}: {[o.name for o in objects]}")
groups={}
for o in objects:groups.setdefault(o.data.as_pointer(),[]).append(o)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper();assets=[];instances=[]
for index,group in enumerate(groups.values(),1):
 source=group[0];base=re.sub(r"_v(639|640|660)(\.\d+)?$","",source.name)
 name=f"{base}_SupportAsset_{index:02d}_v661";target=OUT/f"{name}.fbx"
 bpy.ops.object.select_all(action="DESELECT");source.select_set(True);bpy.context.view_layer.objects.active=source;bpy.ops.object.duplicate();obj=bpy.context.object
 bpy.ops.object.transform_apply(location=False,rotation=True,scale=True);obj.location=(0,0,0);obj.data.transform(Matrix.Scale(100.0,4))
 bpy.ops.export_scene.fbx(filepath=str(target),use_selection=True,object_types={"MESH"},global_scale=1.0,apply_unit_scale=False,
  apply_scale_options="FBX_SCALE_NONE",axis_forward="-Z",axis_up="Y",use_mesh_modifiers=True,mesh_smooth_type="FACE",
  add_leaf_bones=False,bake_anim=False,use_triangles=True)
 dims=[round(v/100.0,4) for v in obj.dimensions]
 assets.append({"asset":name,"fbx":target.name,"sha256":sha(target),"bounds_m":dims,"polygons":len(obj.data.polygons),"source_examples":[o.name for o in group]})
 for member in group:
  role="static_support"
  if "Transfer" in member.name:role="transfer_crossbar"
  elif "Destack" in member.name:role="destack_lift"
  elif "InspectUnload" in member.name:role="unload_robot_arm"
  instances.append({"object":member.name,"asset":name,"location_cm":[round(v*100,3) for v in member.location],
   "rotation_deg":[round(math.degrees(v),3) for v in member.rotation_euler],"role":role})
 bpy.data.objects.remove(obj,do_unlink=True)
report={"revision":"v661","status":"PASS__UNIQUE_SUPPORT_ASSET_STAGING__NOT_PROMOTED","generated_utc":datetime.now(timezone.utc).isoformat(),
 "source":str(SOURCE),"source_sha256":sha(SOURCE),"unique_asset_count":len(assets),"instance_count":len(instances),
 "assets":assets,"instances":instances,"scale_contract":"local geometry explicitly centimetres; actor locations centimetres",
 "protected_map_modified":False,"promotion_authorized":False}
AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps(report,indent=2),encoding="utf-8")
print("LB_TRAIN_A_SUPPORT_V661="+json.dumps({"assets":len(assets),"instances":len(instances)},separators=(",",":")))
