"""Correct v650's double centimetre conversion; preserve v650 as failed evidence."""
import bpy,hashlib,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE=ROOT/r"SourceAssets\Candidate\PressTrains\TrainA\CompleteS03Assembly_v649\CA_MW_PTA_S03_CompleteVisualAssembly_v649.blend"
OUT=ROOT/r"Saved\ImportStaging\CompleteS03_v652";OUT.mkdir(parents=True,exist_ok=True)
FBX=OUT/"SM_CA_MW_PTA_S03_CompleteVisual_v652.fbx";AUDIT=ROOT/r"Saved\Audits\PressTrains\complete_s03_staging_v652.json"
if FBX.exists() or AUDIT.exists():raise RuntimeError("Refusing to overwrite v652")
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
if len(meshes)!=12:raise RuntimeError(f"Expected 12 meshes, got {len(meshes)}")
bpy.ops.object.select_all(action="DESELECT")
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=meshes[0];bpy.ops.object.duplicate();bpy.ops.object.convert(target="MESH")
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);bpy.ops.object.join();master=bpy.context.object
master.name="SM_CA_MW_PTA_S03_CompleteVisual_v652"
bpy.ops.export_scene.fbx(filepath=str(FBX),use_selection=True,object_types={"MESH"},global_scale=1.0,
 apply_unit_scale=True,apply_scale_options="FBX_SCALE_ALL",axis_forward="-Y",axis_up="Z",
 use_mesh_modifiers=True,mesh_smooth_type="FACE",add_leaf_bones=False,bake_anim=False,use_triangles=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
report={"revision":"v652","status":"CORRECTED_STAGING_NOT_PROMOTED","generated_utc":datetime.now(timezone.utc).isoformat(),
 "source":str(SOURCE),"source_sha256":sha(SOURCE),"fbx":str(FBX),"fbx_sha256":sha(FBX),
 "polygons":len(master.data.polygons),"correction":"removed v650 explicit x100 geometry transform",
 "expected_unreal_height_cm":[700,900],"protected_map_modified":False,"promotion_authorized":False}
AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps(report,indent=2),encoding="utf-8")
print("LB_STAGE_V652="+json.dumps(report,separators=(",",":")))
