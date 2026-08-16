"""PIE navigation proof around complete Train A without entering press envelopes."""
import json,time,unreal
from pathlib import Path
from datetime import datetime,timezone
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT=Path(unreal.Paths.project_dir());TARGET="/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainA_RuntimeNav_v663";OUT=ROOT/r"Saved\Audits\PressTrains\complete_train_a_navigation_pie_v664.json"
ROUTES={"operator_aisle":(unreal.Vector(-900,100,30),unreal.Vector(-900,4400,30),4000),"service_aisle":(unreal.Vector(900,100,30),unreal.Vector(900,4400,30),4000),"outfeed_cross_aisle":(unreal.Vector(-900,5100,30),unreal.Vector(900,5100,30),1700)}
PRESS_Y=(750,1500,2250,3000,3750)
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(TARGET):raise RuntimeError("Could not load v663")
unreal.EditorLevelLibrary.editor_play_simulate();started=time.monotonic();handle=None
def row(p):return [round(float(p.x),2),round(float(p.y),2),round(float(p.z),2)]
def protected(p):return abs(p.x)<320 and any(abs(p.y-y)<320 for y in PRESS_Y)
def finish(routes,failures):
 global handle
 if handle:unreal.unregister_slate_post_tick_callback(handle);handle=None
 payload={"revision":"v664","generated_utc":datetime.now(timezone.utc).isoformat(),"target_map":TARGET,"status":"PASS__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED","routes":routes,"press_protected_envelopes_cm":{"x":[-320,320],"station_y":PRESS_Y,"half_y":320},"failures":failures,"protected_map_modified":False,"promotion_authorized":False}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
 (unreal.log if not failures else unreal.log_error)("LINE_BOSS_TRAIN_A_NAV_V664_"+("PASS" if not failures else "FAIL"))
 unreal.EditorLevelLibrary.editor_end_play();unreal.EditorPythonScripting.set_keep_python_script_alive(False);unreal.SystemLibrary.quit_editor()
def tick(_):
 if time.monotonic()-started>60:finish({},["timeout waiting for navmesh"]);return
 if time.monotonic()-started<5:return
 world=unreal.EditorLevelLibrary.get_game_world()
 if not world:return
 boots=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.LBPressShopNavigationBootstrap)
 if len(boots)!=1:finish({},[f"expected one navigation bootstrap, found {len(boots)}"]);return
 routes={};fail=[]
 for name,(start,end,minimum) in ROUTES.items():
  valid=bool(boots[0].validate_path(start,end));points=list(boots[0].get_validated_path_points()) if valid else [];length=float(boots[0].get_validated_path_length()) if valid else None;intrusions=[row(p) for p in points if protected(p)]
  routes[name]={"start_cm":row(start),"end_cm":row(end),"valid":valid,"length_cm":length,"points_cm":[row(p) for p in points],"protected_intrusions":intrusions}
  if not valid:fail.append(name+": invalid or partial path")
  elif length<minimum:fail.append(f"{name}: length {length:.1f} below {minimum}")
  if intrusions:fail.append(f"{name}: enters protected press envelope")
 finish(routes,fail)
handle=unreal.register_slate_post_tick_callback(tick)
