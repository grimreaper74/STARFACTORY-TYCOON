"""Correct v662 helper cubes that used half-extents as Unreal cube scales."""
import json,unreal
from pathlib import Path
ROOT=Path(unreal.Paths.project_dir());BASE="/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainA_RuntimeNav_v670";MAP="/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainA_RuntimeNav_v673";OUT=ROOT/r"Saved\Audits\PressTrains\complete_train_a_proxy_scale_v673.json"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);library=unreal.EditorAssetLibrary
if library.does_asset_exist(MAP) or OUT.exists():raise RuntimeError("Refusing to overwrite v673")
if not levels.new_level_from_template(MAP,BASE):raise RuntimeError("Could not derive v673")
corrected=[]
for a in actors.get_all_level_actors():
 label=a.get_actor_label()
 if label=="LB_TrainA_ReviewFloor":a.set_actor_scale3d(unreal.Vector(22,62,.2));corrected.append(label)
 elif label.endswith("_COLL_Base"):a.set_actor_scale3d(unreal.Vector(9.9,5.3,2.2));corrected.append(label)
 elif label.endswith("_COLL_Upper"):a.set_actor_scale3d(unreal.Vector(9.9,5.3,6.0));corrected.append(label)
 elif any(t in label for t in ("ServiceDeck","RailTop","RailPost","LadderStile","LadderRung")):
  s=a.get_actor_scale3d();a.set_actor_scale3d(unreal.Vector(s.x*2,s.y*2,s.z*2));corrected.append(label)
unreal.SystemLibrary.execute_console_command(unreal.EditorLevelLibrary.get_editor_world(),"RebuildNavigation")
if not levels.save_current_level():raise RuntimeError("Failed saving v673")
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({"revision":"v673","status":"PASS__PROXY_AND_FLOOR_DIMENSIONS_CORRECTED__PIE_PENDING","map":MAP,"source":BASE,"corrected_actor_count":len(corrected),"floor_size_cm":[2200,6200,20],"press_proxy_size_cm":{"base":[990,530,220],"upper":[990,530,600]},"gate_proxy":"unchanged already full-size","protected_map_modified":False,"promotion_authorized":False},indent=2),encoding="utf-8")
unreal.log("LINE_BOSS_COMPLETE_TRAIN_A_PROXY_SCALE_V673_PASS")
