"""Read-only identify remaining large block layers and S07 visuals after v711 stripping."""
from pathlib import Path
import json,unreal
ROOT=Path(unreal.Paths.project_dir());MAP="/Game/LineBoss/Developer/Validation/PressShop/LB_PressShop_StrippedNewPresses_v711";OUT=ROOT/"Saved/Audits/PressShopIntegration/press_shop_remaining_block_visuals_v713.json"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def tags(a):return {str(t) for t in a.tags}
if OUT.exists():raise RuntimeError("Refusing overwrite v713")
if not levels.load_level(MAP):raise RuntimeError(MAP)
rows=[];s07=[]
for a in api.get_all_level_actors():
 t=tags(a)
 if "LB.PressTrain.Installed.TRAIN_A" not in t:continue
 comp=a.get_component_by_class(unreal.StaticMeshComponent)
 if not comp:continue
 o,e=a.get_actor_bounds(False,False);mesh=comp.get_editor_property("static_mesh")
 row={"label":a.get_actor_label(),"mesh":mesh.get_path_name() if mesh else None,"location_cm":list(a.get_actor_location().to_tuple()),"bounds_origin_cm":list(o.to_tuple()),"bounds_extent_cm":list(e.to_tuple()),"volume_proxy":e.x*e.y*e.z,"hidden_in_game":bool(comp.get_editor_property("hidden_in_game")),"visible":bool(comp.get_editor_property("visible")),"materials":[m.get_path_name() if m else None for m in comp.get_materials()],"tags":sorted(t)}
 rows.append(row)
 if "LB.PressTrain.Stage.S07" in t:s07.append(row)
payload={"revision":"v713","status":"PASS__READ_ONLY_REMAINING_VISUAL_INVENTORY","map":MAP,"largest_train_a_visuals":sorted(rows,key=lambda r:r["volume_proxy"],reverse=True)[:40],"train_a_s07_visuals":sorted(s07,key=lambda r:r["volume_proxy"],reverse=True)}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8");unreal.log("LINE_BOSS_REMAINING_BLOCK_VISUALS_V713_PASS");unreal.SystemLibrary.quit_editor()
