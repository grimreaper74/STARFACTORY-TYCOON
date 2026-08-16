"""Export v649 S03 as separate local-pivot FBXs for runtime binding."""
import bpy,hashlib,json,re
from pathlib import Path
from datetime import datetime,timezone
from mathutils import Matrix,Vector
ROOT=Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE=ROOT/r"SourceAssets\Candidate\PressTrains\TrainA\CompleteS03Assembly_v649\CA_MW_PTA_S03_CompleteVisualAssembly_v649.blend"
OUT=ROOT/r"Saved\ImportStaging\CompleteS03Modular_v654";OUT.mkdir(parents=True,exist_ok=True)
AUDIT=ROOT/r"Saved\Audits\PressTrains\complete_s03_modular_staging_v654.json"
if AUDIT.exists():raise RuntimeError("Refusing to overwrite v654")
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));objects=sorted((o for o in bpy.context.scene.objects if o.type=="MESH"),key=lambda o:o.name)
if len(objects)!=12:raise RuntimeError(f"Expected 12 meshes, got {len(objects)}")
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
rows=[]
for source in objects:
 name="SM_CA_MW_"+re.sub(r"[^A-Za-z0-9_]+","_",source.name)+"_v654"
 target=OUT/f"{name}.fbx"
 if target.exists():raise RuntimeError(f"Refusing to overwrite {target}")
 bpy.ops.object.select_all(action="DESELECT");source.select_set(True);bpy.context.view_layer.objects.active=source
 bpy.ops.object.duplicate();obj=bpy.context.object
 actor_location=Vector(source.location)
 bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
 obj.location=(0,0,0);pivot="object_center"
 if "Gate" in source.name:
  # v648 gate hinges are on the negative local-X edge; after the v649 90-degree
  # facing rotation this is the negative world-Y edge.
  min_y=min(v.co.y for v in obj.data.vertices)
  obj.data.transform(Matrix.Translation((0,-min_y,0)))
  actor_location.y+=min_y;pivot="negative_y_hinge_edge"
 bpy.ops.export_scene.fbx(filepath=str(target),use_selection=True,object_types={"MESH"},global_scale=1.0,
  apply_unit_scale=True,apply_scale_options="FBX_SCALE_ALL",axis_forward="-Y",axis_up="Z",
  use_mesh_modifiers=True,mesh_smooth_type="FACE",add_leaf_bones=False,bake_anim=False,use_triangles=True)
 role="static"
 if "RamSlide" in source.name:role="moving_press_slide"
 elif "UpperDie" in source.name:role="moving_upper_die"
 elif "Gate" in source.name:role="access_gate"
 elif "Rotor" in source.name:role="flywheel_rotor"
 rows.append({"source_object":source.name,"asset":name,"fbx":target.name,"sha256":sha(target),
  "actor_location_cm":[round(v*100,3) for v in actor_location],"actor_rotation_deg":[0,0,0],
  "bounds_m":[round(v,4) for v in obj.dimensions],"polygons":len(obj.data.polygons),"pivot":pivot,"role":role})
 bpy.data.objects.remove(obj,do_unlink=True)
report={"revision":"v654","status":"PASS__MODULAR_LOCAL_PIVOT_STAGING__NOT_PROMOTED",
 "generated_utc":datetime.now(timezone.utc).isoformat(),"source":str(SOURCE),"source_sha256":sha(SOURCE),
 "asset_count":len(rows),"assets":rows,"scale_contract":"metres via FBX scene units; Unreal bounds must equal cm",
 "protected_map_modified":False,"promotion_authorized":False}
AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps(report,indent=2),encoding="utf-8")
print("LB_STAGE_V654="+json.dumps({"status":report["status"],"assets":len(rows)},separators=(",",":")))
