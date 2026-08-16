"""Bake the proven Unreal reflection/rotation into a new Train A FBX source."""
import bpy, hashlib, json, math
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/ModularAssembly_v037/CA_MW_PressTrainA_ModularAssembly_v037.blend"
SRC_SHA="D4C7D36DB98CF728317FBBC05E8AE49EEA945ED9026F624739D95584D3DFCDF8"
OUT=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/UnrealAxisBaked_v039";FBX=OUT/"FBX";BLEND=OUT/"CA_MW_PressTrainA_UnrealAxisBaked_v039.blend";REPORT=OUT/"PRESS_TRAIN_A_UNREAL_AXIS_BAKED_v039.json"
for d in (OUT,FBX):d.mkdir(parents=True,exist_ok=True)
if BLEND.exists() or REPORT.exists() or any(FBX.glob("*.fbx")):raise RuntimeError("refusing to overwrite v039")
def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for chunk in iter(lambda:f.read(1048576),b""):h.update(chunk)
 return h.hexdigest().upper()
if sha(SRC)!=SRC_SHA:raise RuntimeError("v037 blend hash drift")
bpy.ops.wm.open_mainfile(filepath=str(SRC))
for obj in list(bpy.data.objects):
 if obj.type in {"LIGHT","CAMERA"}:bpy.data.objects.remove(obj,do_unlink=True)
geo=[o for o in bpy.data.objects if o.type in {"MESH","CURVE","FONT"} and not o.hide_render and not o.name.startswith("SM_CA_MW_PressTrainA_ModularAssembly")]
bpy.ops.object.select_all(action="DESELECT")
for o in geo:o.select_set(True)
bpy.context.view_layer.objects.active=next(o for o in geo if o.type=="MESH")
bpy.ops.object.duplicate()
for o in list(bpy.context.selected_objects):
 if o.type in {"CURVE","FONT"}:
  bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target="MESH")
bpy.ops.object.join();combined=bpy.context.object;combined.name="SM_CA_MW_PressTrainA_UnrealAxisBaked_v039"
# Equivalent to the visually proven Unreal -90 degree X rotation plus negative-Y reflection,
# baked into vertices so Unreal can use a positive actor scale and stable normals/collision.
combined.scale.y=-1.0;combined.rotation_euler.x=-math.pi/2
bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND),check_existing=False)
fbx=FBX/f"{combined.name}.fbx"
bpy.ops.object.select_all(action="DESELECT");combined.select_set(True);bpy.context.view_layer.objects.active=combined
bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,apply_unit_scale=True,apply_scale_options="FBX_SCALE_ALL",axis_forward="-Y",axis_up="Z",use_mesh_modifiers=True,mesh_smooth_type="FACE",add_leaf_bones=False,use_custom_props=True,object_types={"MESH"})
dims=combined.dimensions
payload={"$schema":"cairnwell/source/press-train-a-unreal-axis-baked-v039/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"SOURCE_ONLY_AXIS_AND_HANDEDNESS_BAKED__ISOLATED_UNREAL_REIMPORT_REQUIRED__NOT_PROMOTED","source_parent":str(SRC.relative_to(ROOT)).replace('\\','/'),"source_parent_sha256":SRC_SHA,"baked_transform":{"rotation_x_degrees":-90,"scale_y_reflection":-1},"combined_dimensions_m":[dims.x,dims.y,dims.z],"engineering_values":"TBC_NOT_INVENTED","runtime_authority_added":False,"promotion_authorized":False,"blend_sha256":sha(BLEND),"fbx_sha256":sha(fbx),"fbx_bytes":fbx.stat().st_size}
REPORT.write_text(json.dumps(payload,indent=2),encoding="utf-8");print(json.dumps(payload,indent=2))
