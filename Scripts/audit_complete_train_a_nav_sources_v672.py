import json,unreal
from pathlib import Path
ROOT=Path(unreal.Paths.project_dir());MAP="/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainA_RuntimeNav_v670";OUT=ROOT/r"Saved\Audits\PressTrains\complete_train_a_nav_sources_v672.json"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):raise RuntimeError("Could not load v670")
rows=[]
for a in actors.get_all_level_actors():
 if a.get_actor_label() in ("LB_TrainA_ReviewFloor","LB_TrainA_NavBounds_v662") or isinstance(a,unreal.RecastNavMesh):
  origin,extent=a.get_actor_bounds(False,False);comp=a.get_component_by_class(unreal.StaticMeshComponent)
  rows.append({"label":a.get_actor_label(),"class":a.get_class().get_name(),"origin":[origin.x,origin.y,origin.z],"size":[extent.x*2,extent.y*2,extent.z*2],"collision":str(comp.get_collision_enabled()) if comp else None,"profile":str(comp.get_collision_profile_name()) if comp else None,"affects_navigation":bool(comp.get_editor_property("can_ever_affect_navigation")) if comp else None,"hidden_editor":a.is_temporarily_hidden_in_editor()})
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({"revision":"v672","map":MAP,"rows":rows},indent=2),encoding="utf-8");unreal.log("LINE_BOSS_TRAIN_A_NAV_SOURCE_AUDIT_V672")
