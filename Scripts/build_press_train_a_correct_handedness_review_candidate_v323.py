"""Test upright -90 X conversion with positive Y scale to preserve authored handedness."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir());BASE="/Game/LineBoss/Maps/LB_PressTrainA_IsolatedStudioCandidate_v307";MAP="/Game/LineBoss/Maps/LB_PressTrainA_DoubleMirrorReviewCandidate_v324";BASE_FILE=ROOT/"Content/LineBoss/Maps/LB_PressTrainA_IsolatedStudioCandidate_v307.umap";MAP_FILE=ROOT/"Content/LineBoss/Maps/LB_PressTrainA_DoubleMirrorReviewCandidate_v324.umap";OUT=ROOT/"Saved/Audits/PressTrains/press_train_a_double_mirror_review_build_v324.json";BASE_SHA=hashlib.sha256(BASE_FILE.read_bytes()).hexdigest().upper();lib=unreal.EditorAssetLibrary;levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if lib.does_asset_exist(MAP) or OUT.exists():raise RuntimeError("refusing to overwrite v324")
if not levels.new_level_from_template(MAP,BASE):raise RuntimeError("fresh v307 child failed")
candidate=next((a for a in api.get_all_level_actors() if "LB.PressTrain.TrainA.ModularSource.v037" in {str(t) for t in a.tags}),None)
if candidate is None:raise RuntimeError("candidate missing")
candidate.set_actor_scale3d(unreal.Vector(-100.0,-100.0,100.0));candidate.set_actor_rotation(unreal.Rotator(-90.0,0.0,0.0),False);origin,extent=candidate.get_actor_bounds(False);candidate.add_actor_world_offset(unreal.Vector(0,0,-(origin.z-extent.z)),False,False);origin,extent=candidate.get_actor_bounds(False)
for i,x in enumerate((origin.x-2200,origin.x-750,origin.x+750,origin.x+2200),1):
 for side,y in (("front",origin.y-950),("rear",origin.y+950)):
  light=api.spawn_actor_from_class(unreal.PointLight,unreal.Vector(x,y,origin.z+620),unreal.Rotator());light.set_actor_label(f"LB_V324_MOVABLE_{side.upper()}_{i:02d}");light.point_light_component.set_mobility(unreal.ComponentMobility.MOVABLE);light.point_light_component.set_editor_properties({"intensity":85000.0,"attenuation_radius":3000.0,"source_radius":160.0,"soft_source_radius":320.0,"cast_shadows":False})
for actor in api.get_all_level_actors():
 if actor.get_actor_label() not in ("LB_V307_CAM_Operator","LB_V307_CAM_Rear","LB_V307_CAM_Elevated"):continue
 settings=actor.camera_component.get_editor_property("post_process_settings");settings.set_editor_properties({"override_auto_exposure_method":True,"auto_exposure_method":unreal.AutoExposureMethod.AEM_BASIC,"override_auto_exposure_min_brightness":True,"override_auto_exposure_max_brightness":True,"auto_exposure_min_brightness":1.0,"auto_exposure_max_brightness":1.0,"override_auto_exposure_bias":True,"auto_exposure_bias":3.5});actor.camera_component.set_editor_property("post_process_settings",settings);actor.camera_component.set_editor_property("post_process_blend_weight",1.0)
fail=[];floor_z=origin.z-extent.z
if abs(floor_z)>1.0:fail.append(f"floor z {floor_z}")
if not levels.save_current_level():fail.append("save failed")
if hashlib.sha256(BASE_FILE.read_bytes()).hexdigest().upper()!=BASE_SHA:fail.append("v307 changed")
payload={"$schema":"cairnwell/audit/press-train-a-double-mirror-review-v324/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"PASS__DOUBLE_MIRROR_VISUAL_REVIEW_READY__NOT_PROMOTED" if not fail else "FAIL__V324_NOT_EVIDENCE","base":BASE,"base_sha256":BASE_SHA,"map":MAP,"map_sha256":hashlib.sha256(MAP_FILE.read_bytes()).hexdigest().upper() if MAP_FILE.exists() else None,"candidate_rotation":"X/roll -90 degrees","candidate_scale":[-100,-100,100],"candidate_origin":[origin.x,origin.y,origin.z],"candidate_extent":[extent.x,extent.y,extent.z],"candidate_floor_z":floor_z,"geometry_changed":False,"runtime_authority_changed":False,"promotion_authorized":False,"failures":fail};OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8");print(json.dumps(payload,indent=2))
if fail:raise RuntimeError("; ".join(fail))
unreal.SystemLibrary.quit_editor()
