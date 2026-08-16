from pathlib import Path
import json,unreal
ROOT=Path(unreal.Paths.project_dir());MAP="/Game/LineBoss/Maps/LB_PressShop_CleanInboundSupportFleetRuntime_v20260809_v052";OUT=ROOT/"Saved/Audits/PressShopIntegration/clean_support_fleet_classes_v20260809_v054.json"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):raise RuntimeError("load failed")
rows=[]
for a in actors.get_all_level_actors():
 if "Robot_" in a.get_actor_label() or "SUPPORT_FLEET" in a.get_actor_label():rows.append({"label":a.get_actor_label(),"class":a.get_class().get_name(),"class_path":a.get_class().get_path_name(),"tags":[str(x) for x in a.tags]})
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({"map":MAP,"actors":rows},indent=2),encoding="utf-8")
