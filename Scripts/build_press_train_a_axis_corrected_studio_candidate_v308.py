"""Build v309: rotate the tipped v037 intake around Unreal roll/X.

v308 is retained as a rejected yaw-axis experiment.
"""
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
BASE="/Game/LineBoss/Maps/LB_PressTrainA_IsolatedStudioCandidate_v307"
MAP="/Game/LineBoss/Maps/LB_PressTrainA_AxisCorrectedStudioCandidate_v309"
BASE_FILE=ROOT/"Content/LineBoss/Maps/LB_PressTrainA_IsolatedStudioCandidate_v307.umap"
MAP_FILE=ROOT/"Content/LineBoss/Maps/LB_PressTrainA_AxisCorrectedStudioCandidate_v309.umap"
BASE_SHA="F115CAB08B7C319219AC633B0DA61B477128A80689FDB92D143C9B607ADD7571"
OUT=ROOT/"Saved/Audits/PressTrains/press_train_a_axis_corrected_studio_build_v309.json"
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest().upper()
if sha(BASE_FILE)!=BASE_SHA: raise RuntimeError("v307 hash drift")
lib=unreal.EditorAssetLibrary; levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if lib.does_asset_exist(MAP) or OUT.exists(): raise RuntimeError("refusing to overwrite v309")
if not levels.new_level_from_template(MAP,BASE): raise RuntimeError("fresh v307 child failed")
actors=api.get_all_level_actors()
candidate=next((a for a in actors if "LB.PressTrain.TrainA.ModularSource.v037" in {str(t) for t in a.tags}),None)
if candidate is None: raise RuntimeError("candidate missing")
candidate.set_actor_rotation(unreal.Rotator(90.0,0.0,0.0),False)
loc=candidate.get_actor_location(); candidate.set_actor_location(unreal.Vector(loc.x,loc.y,0.0),False,False)
o,e=candidate.get_actor_bounds(False); correction=-(o.z-e.z)
loc=candidate.get_actor_location(); candidate.set_actor_location(unreal.Vector(loc.x,loc.y,loc.z+correction),False,False)
candidate.tags=list(candidate.tags)+[unreal.Name("LB.ImportAxis.RollPositive90.v309"),unreal.Name("LB.Asset.Candidate.v309")]
o,e=candidate.get_actor_bounds(False); centre=(o.x,o.y,o.z)
for actor in actors:
 if isinstance(actor,unreal.CameraActor): api.destroy_actor(actor)
def camera(label,location,target,ortho=None,fov=68.0):
 c=api.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(*location),unreal.Rotator());c.set_actor_label(label);c.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(c.get_actor_location(),unreal.Vector(*target)),False)
 props={"aspect_ratio":16/9,"constrain_aspect_ratio":True}
 if ortho is not None: props.update({"projection_mode":unreal.CameraProjectionMode.ORTHOGRAPHIC,"ortho_width":ortho})
 else: props["field_of_view"]=fov
 c.camera_component.set_editor_properties(props);return c
camera("LB_V309_CAM_Operator",(o.x,o.y-2200,o.z),centre,6200.0)
camera("LB_V309_CAM_Rear",(o.x,o.y+2200,o.z),centre,6200.0)
camera("LB_V309_CAM_Elevated",(o.x+3600,o.y-3200,o.z+1700),centre,None,68.0)
floor_z=o.z-e.z;fail=[]
if abs(floor_z)>1:fail.append(f"floor z {floor_z}")
if not levels.save_current_level():fail.append("save failed")
if sha(BASE_FILE)!=BASE_SHA:fail.append("v307 changed")
payload={"$schema":"cairnwell/audit/press-train-a-axis-corrected-studio-v309/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"PASS__ROLL_X_POSITIVE_90_VISUAL_GATE_READY__NOT_PROMOTED" if not fail else "FAIL__V309_NOT_EVIDENCE","base":BASE,"base_sha256":BASE_SHA,"map":MAP,"map_sha256":sha(MAP_FILE) if MAP_FILE.exists() else None,"axis_correction":{"unreal_rotator_first_component_degrees":90.0,"intended_axis":"roll_x"},"candidate_origin":[o.x,o.y,o.z],"candidate_extent":[e.x,e.y,e.z],"floor_z":floor_z,"promotion_authorized":False,"failures":fail};OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8");print(json.dumps(payload,indent=2))
if fail:raise RuntimeError("; ".join(fail))
unreal.SystemLibrary.quit_editor()
