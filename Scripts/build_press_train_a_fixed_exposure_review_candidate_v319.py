"""Create a camera-only fixed-exposure successor for upright Train A review."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir());BASE="/Game/LineBoss/Maps/LB_PressTrainA_MovableLitReviewCandidate_v315";MAP="/Game/LineBoss/Maps/LB_PressTrainA_FixedExposureReviewCandidate_v319"
BASE_FILE=ROOT/"Content/LineBoss/Maps/LB_PressTrainA_MovableLitReviewCandidate_v315.umap";MAP_FILE=ROOT/"Content/LineBoss/Maps/LB_PressTrainA_FixedExposureReviewCandidate_v319.umap";OUT=ROOT/"Saved/Audits/PressTrains/press_train_a_fixed_exposure_review_build_v319.json"
BASE_SHA=hashlib.sha256(BASE_FILE.read_bytes()).hexdigest().upper()
lib=unreal.EditorAssetLibrary;levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if lib.does_asset_exist(MAP) or OUT.exists():raise RuntimeError("refusing to overwrite v319")
if not levels.new_level_from_template(MAP,BASE):raise RuntimeError("fresh v315 child failed")
changed=[]
for actor in api.get_all_level_actors():
 if actor.get_actor_label() not in ("LB_V309_CAM_Operator","LB_V309_CAM_Rear","LB_V309_CAM_Elevated"):continue
 comp=actor.camera_component;settings=comp.get_editor_property("post_process_settings")
 settings.set_editor_properties({"override_auto_exposure_method":True,"auto_exposure_method":unreal.AutoExposureMethod.AEM_BASIC,"override_auto_exposure_min_brightness":True,"override_auto_exposure_max_brightness":True,"auto_exposure_min_brightness":1.0,"auto_exposure_max_brightness":1.0,"override_auto_exposure_bias":True,"auto_exposure_bias":3.5})
 comp.set_editor_property("post_process_settings",settings);comp.set_editor_property("post_process_blend_weight",1.0);changed.append(actor.get_actor_label())
fail=[]
if len(changed)!=3:fail.append(f"camera count {len(changed)}")
if not levels.save_current_level():fail.append("save failed")
if hashlib.sha256(BASE_FILE.read_bytes()).hexdigest().upper()!=BASE_SHA:fail.append("v315 changed")
payload={"$schema":"cairnwell/audit/press-train-a-fixed-exposure-review-v319/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"PASS__CAMERA_ONLY_FIXED_EXPOSURE_REVIEW_READY__NOT_PROMOTED" if not fail else "FAIL__V319_NOT_EVIDENCE","base":BASE,"base_sha256":BASE_SHA,"map":MAP,"map_sha256":hashlib.sha256(MAP_FILE.read_bytes()).hexdigest().upper() if MAP_FILE.exists() else None,"camera_labels":changed,"fixed_exposure_bias":3.5,"geometry_changed":False,"materials_changed":False,"runtime_authority_changed":False,"promotion_authorized":False,"failures":fail}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8");print(json.dumps(payload,indent=2))
if fail:raise RuntimeError("; ".join(fail))
unreal.SystemLibrary.quit_editor()
