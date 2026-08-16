"""Stage the complete v649 S03 visual assembly as a fresh Unreal intake FBX."""
import bpy
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE=ROOT/r"SourceAssets\Candidate\PressTrains\TrainA\CompleteS03Assembly_v649\CA_MW_PTA_S03_CompleteVisualAssembly_v649.blend"
OUT=ROOT/r"Saved\ImportStaging\CompleteS03_v650"
AUDIT=ROOT/r"Saved\Audits\PressTrains\complete_s03_staging_v650.json"
OUT.mkdir(parents=True,exist_ok=True);AUDIT.parent.mkdir(parents=True,exist_ok=True)
FBX=OUT/"SM_CA_MW_PTA_S03_CompleteVisual_v650.fbx"
if FBX.exists() or AUDIT.exists(): raise RuntimeError("Refusing to overwrite v650")
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
if len(meshes)!=12: raise RuntimeError(f"Expected shell plus 11 modules, got {len(meshes)}")
bpy.ops.object.select_all(action="DESELECT")
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=meshes[0]
bpy.ops.object.duplicate()
dupes=[o for o in bpy.context.selected_objects if o.type=="MESH"]
bpy.ops.object.convert(target="MESH")
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
bpy.ops.object.join();master=bpy.context.object;master.name="SM_CA_MW_PTA_S03_CompleteVisual_v650"
# Established Line Boss FBX route exports centimetre geometry explicitly.
master.data.transform(__import__('mathutils').Matrix.Scale(100.0,4))
bpy.ops.export_scene.fbx(filepath=str(FBX),use_selection=True,object_types={"MESH"},
 global_scale=1.0,apply_unit_scale=False,apply_scale_options="FBX_SCALE_NONE",
 axis_forward="-Z",axis_up="Y",use_mesh_modifiers=True,mesh_smooth_type="FACE",
 add_leaf_bones=False,bake_anim=False,use_triangles=True,path_mode="AUTO")
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
report={"revision":"v650","status":"STAGED_FOR_ISOLATED_UNREAL_INTAKE_NOT_PROMOTED",
 "generated_utc":datetime.now(timezone.utc).isoformat(),"source":str(SOURCE),"source_sha256":sha(SOURCE),
 "fbx":str(FBX),"fbx_sha256":sha(FBX),"source_meshes":len(meshes),"polygons":len(master.data.polygons),
 "scale_contract":"Blender metres multiplied 100 to Unreal centimetres; verify import bounds 700-900 cm Z",
 "combined_visual_only":True,"moving_part_runtime_import":"pending modular staging",
 "protected_map_modified":False,"promotion_authorized":False}
AUDIT.write_text(json.dumps(report,indent=2),encoding="utf-8")
print("LB_STAGE_V650="+json.dumps(report,separators=(",",":")))
