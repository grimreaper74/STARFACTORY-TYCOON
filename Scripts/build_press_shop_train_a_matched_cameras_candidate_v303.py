"""Camera-only child of v302 for Pro-matched Train A visual judgment."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir());BASE="/Game/LineBoss/Maps/LB_PressShop_TrainAModularVisualIntakeCandidate_v302";MAP="/Game/LineBoss/Maps/LB_PressShop_TrainAModularMatchedCamerasCandidate_v303"
BASE_FILE=ROOT/"Content/LineBoss/Maps/LB_PressShop_TrainAModularVisualIntakeCandidate_v302.umap";MAP_FILE=ROOT/"Content/LineBoss/Maps/LB_PressShop_TrainAModularMatchedCamerasCandidate_v303.umap";BASE_SHA="6C2B62AC340A394B122FAA05C99FD76277C0F4B938FCC282D3EB17F221F0D173";OUT=ROOT/"Saved/Audits/PressTrains/press_train_a_matched_cameras_build_v303.json"
CAMERAS=[("LB_V303_CAM_TrainAOperatorMatched",(4388,-6200,620),(4388,-4300,455),58.0),("LB_V303_CAM_TrainARearMatched",(4388,-2400,620),(4388,-4300,455),58.0),("LB_V303_CAM_TrainAElevatedMatched",(7300,-6500,1650),(4300,-4300,430),60.0)]
def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for c in iter(lambda:f.read(1048576),b""):h.update(c)
 return h.hexdigest().upper()
lib=unreal.EditorAssetLibrary;levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if sha(BASE_FILE)!=BASE_SHA:raise RuntimeError("v302 hash drift")
if lib.does_asset_exist(MAP) or OUT.exists():raise RuntimeError("refusing to overwrite v303")
if not levels.new_level_from_template(MAP,BASE):raise RuntimeError("fresh v302 child failed")
rows=[]
for label,location,target,fov in CAMERAS:
 camera=api.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(*location),unreal.Rotator());camera.set_actor_label(label);camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(),unreal.Vector(*target)),False);camera.camera_component.set_editor_properties({"field_of_view":fov,"aspect_ratio":16/9,"constrain_aspect_ratio":True});camera.tags=[unreal.Name(x) for x in ("LB.Camera.Validation","LB.Camera.Fixed.ProMatched.v303","LB.Asset.Candidate.v303","LB.Asset.CandidateNotPromoted")];rows.append({"label":label,"location_cm":location,"target_cm":target,"fov":fov})
fail=[]
candidate=[a for a in api.get_all_level_actors() if "LB.PressTrain.TrainA.ModularSource.v037" in {str(t) for t in a.tags}]
if len(candidate)!=1:fail.append(f"candidate count {len(candidate)}")
if not levels.save_current_level():fail.append("save failed")
if sha(BASE_FILE)!=BASE_SHA:fail.append("protected v302 changed")
payload={"$schema":"cairnwell/audit/press-train-a-matched-cameras-v303/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"PASS__CAMERA_ONLY_PRO_MATCHED_CHILD__FRESH_VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not fail else "FAIL__V303_NOT_A_PARENT","base":BASE,"base_sha256":BASE_SHA,"map":MAP,"map_sha256":sha(MAP_FILE) if MAP_FILE.exists() else None,"cameras":rows,"candidate_count":len(candidate),"geometry_changed":False,"runtime_authority_changed":False,"promotion_authorized":False,"failures":fail};OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8");print(json.dumps(payload,indent=2))
if fail:raise RuntimeError("; ".join(fail))
unreal.SystemLibrary.quit_editor()
