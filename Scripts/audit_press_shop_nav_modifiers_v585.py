from pathlib import Path
import json,unreal
MAP="/Game/LineBoss/Developer/Validation/LB_PressShop_InboundNavCandidate_v581"
OUT=Path(unreal.Paths.project_saved_dir())/"Audits/PressShopIntegration/nav_modifiers_v585.json"
l=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);a=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not l.load_level(MAP):raise RuntimeError(MAP)
rows=[]
for x in a.get_all_level_actors():
 if isinstance(x,unreal.NavModifierVolume) or isinstance(x,unreal.NavMeshBoundsVolume):
  o,e=x.get_actor_bounds(False,False);rows.append({"label":x.get_actor_label(),"class":x.get_class().get_name(),"origin":[o.x,o.y,o.z],"extent":[e.x,e.y,e.z]})
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(rows,indent=2),encoding="utf-8")
