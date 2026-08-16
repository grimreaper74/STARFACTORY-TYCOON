"""Fresh lit visual-review derivative of the passing v673 runtime/nav map."""
import json,unreal
from pathlib import Path
ROOT=Path(unreal.Paths.project_dir());BASE="/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainA_RuntimeNav_v673";MAP="/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainA_VisualReview_v678";OUT=ROOT/r"Saved\Audits\PressTrains\complete_train_a_visual_review_build_v678.json"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);library=unreal.EditorAssetLibrary
if library.does_asset_exist(MAP) or OUT.exists():raise RuntimeError("Refusing to overwrite v678")
if not levels.new_level_from_template(MAP,BASE):raise RuntimeError("Could not derive v678")
hidden=0
for a in actors.get_all_level_actors():
 if unreal.Name("LB.Collision.Proxy") in a.tags:a.set_actor_hidden_in_game(True);a.set_is_temporarily_hidden_in_editor(True);hidden+=1
def camera(label,loc,target,fov):
 a=actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(*loc),unreal.Rotator());a.set_actor_label(label);a.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*loc),unreal.Vector(*target)),False);a.camera_component.set_editor_property("field_of_view",fov);a.tags=[unreal.Name("LB.VisualGate.FixedCamera"),unreal.Name("LB.Asset.CandidateNotPromoted")];return a
camera("LB_CAM_TrainA_OperatorOverview_v678",(-7600,2250,2300),(0,2250,350),42)
camera("LB_CAM_TrainA_ElevatedProcess_v678",(-6200,-1500,3400),(0,2300,300),48)
camera("LB_CAM_TrainA_ServiceOverview_v678",(7200,2250,2100),(0,2250,350),43)
sun=actors.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,2250,2500),unreal.Rotator(-42,-35,0));sun.set_actor_label("LB_TrainA_KeyLight_v678");sun.directional_light_component.set_editor_property("intensity",7.0)
sky=actors.spawn_actor_from_class(unreal.SkyLight,unreal.Vector(0,2250,1600),unreal.Rotator());sky.set_actor_label("LB_TrainA_SkyLight_v678");sky.get_component_by_class(unreal.SkyLightComponent).set_editor_properties({"intensity":1.25,"real_time_capture":True})
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():raise RuntimeError("Failed saving v678")
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({"revision":"v678","status":"PASS__FRESH_FIXED_CAMERA_REVIEW_MAP__CAPTURE_PENDING","map":MAP,"source":BASE,"fixed_cameras":3,"collision_proxies_hidden_visual_only":hidden,"gameplay_collision_unchanged":True,"protected_map_modified":False,"promotion_authorized":False},indent=2),encoding="utf-8")
unreal.log("LINE_BOSS_COMPLETE_TRAIN_A_VISUAL_BUILD_V678_PASS")
