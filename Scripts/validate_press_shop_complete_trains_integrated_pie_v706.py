"""PIE proof that integrated complete A-D identities, commands and separated movers coexist."""
from pathlib import Path
from datetime import datetime,timezone
import json,time,unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT=Path(unreal.Paths.project_dir());MAP="/Game/LineBoss/Developer/Validation/PressShop/LB_PressShop_CompleteTrainsABCD_Visual_v702"
OUT=ROOT/"Saved/Audits/PressShopIntegration/press_shop_complete_trains_integrated_pie_v706.json"
FAMILIES={"A":"LARGE OUTER PANELS","B":"FLOORS / UNDERBODY","C":"CLOSURES","D":"REINFORCEMENTS / SMALL PANELS"}
AUTH=unreal.Name("CW.MW.CONTROL_ROOM");levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if OUT.exists():raise RuntimeError("Refusing overwrite v706")
if not levels.load_level(MAP):raise RuntimeError(MAP)
unreal.EditorLevelLibrary.editor_play_simulate();started=time.monotonic();handle=None;state="discover";trains={};motion={};rest={};checks={};failures=[];completed=set()
def tags(a):return {str(t) for t in a.tags}
def dist(a,b):return (a-b).length()
def adelta(a,b):return abs((a-b+180)%360-180)
def finish():
 global handle
 if handle:unreal.unregister_slate_post_tick_callback(handle);handle=None
 for letter in "ABCD":
  checks[f"train_{letter}_completed_cycle"]=letter in completed
  checks[f"train_{letter}_destack_moves"]=motion.get(letter,{}).get("destack",0)>5
  checks[f"train_{letter}_four_transfers_move"]=motion.get(letter,{}).get("transfer",0)>10
  checks[f"train_{letter}_unload_robot_moves"]=motion.get(letter,{}).get("unload",0)>5
 failures.extend(k for k,v in checks.items() if not v and k not in failures)
 payload={"revision":"v706","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"PASS__FOUR_INTEGRATED_COMPLETE_TRAINS_AUTHORITY_PROCESS_AND_MOTION" if not failures else "FAIL__V706",
  "map":MAP,"checks":checks,"motion_metrics":motion,"completed_trains":sorted(completed),"failures":failures,"meshy_credits_used":0,"protected_map_modified":False}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8");(unreal.log if not failures else unreal.log_error)("LINE_BOSS_PRESS_SHOP_COMPLETE_TRAINS_INTEGRATED_PIE_V706_"+("PASS" if not failures else "FAIL"));unreal.EditorLevelLibrary.editor_end_play();unreal.EditorPythonScripting.set_keep_python_script_alive(False);unreal.SystemLibrary.quit_editor()
def tick(_):
 global state,trains,motion,rest
 now=time.monotonic()
 if now-started>70:failures.append("timeout at "+state);finish();return
 world=unreal.EditorLevelLibrary.get_game_world()
 if not world:return
 authorities=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.LBPressTrainAStation)
 if state=="discover":
  if len(authorities)!=4 or now-started<3:return
  for train in authorities:
   tid=str(train.get_hmi_status().train_id);letter=tid[-1] if tid.startswith("TRAIN_") else "?"
   if letter in trains:failures.append("duplicate identity "+tid)
   trains[letter]=train
  checks["exactly_four_native_authorities"]=len(authorities)==4;checks["unique_identities_A_D"]=set(trains)==set("ABCD")
  statics=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.StaticMeshActor)
  for letter in "ABCD":
   train=trains.get(letter)
   if not train:continue
   scope=f"LB.PressTrain.Installed.TRAIN_{letter}"
   roles={"destack":[a for a in statics if scope in tags(a) and "LB.PressTrain.Role.destack_lift" in tags(a)],
          "transfer":[a for a in statics if scope in tags(a) and "LB.PressTrain.Role.transfer_crossbar" in tags(a)],
          "unload":[a for a in statics if scope in tags(a) and "LB.PressTrain.Role.unload_robot_shoulder_runtime" in tags(a)]}
   checks[f"train_{letter}_identity"]=str(train.get_hmi_status().train_id)==f"TRAIN_{letter}"
   checks[f"train_{letter}_family"]=train.get_part_family()==FAMILIES[letter]
   checks[f"train_{letter}_role_counts"]=len(roles["destack"])==3 and len(roles["transfer"])==4 and len(roles["unload"])==1
   rest[letter]={"roles":roles,"destack":[(a,a.get_actor_location()) for a in roles["destack"]],"transfer":[(a,a.get_actor_location()) for a in roles["transfer"]],"unload":roles["unload"][0].get_actor_rotation().yaw if roles["unload"] else 0}
   motion[letter]={"destack":0.0,"transfer":0.0,"unload":0.0}
   train.set_access_interlocks_closed(True);train.set_safety_circuit_healthy(True);train.set_emergency_stop_active(False);train.set_destack_healthy(True);train.set_transfer_healthy(True);train.set_hydraulic_pressure(280);train.set_press_load(45);train.set_inspection_healthy(True);train.set_stillage_output_clear(True);train.set_target_strokes_per_minute(10)
   checks[f"train_{letter}_blank_accepted"]=bool(train.queue_reserved_blank(unreal.Name(f"RES-V706-{letter}"),unreal.Name(f"BLANK-V706-{letter}")))
   source=unreal.Name(f"MW.MCR.TRAIN_{letter}.CONSOLE");checks[f"train_{letter}_power_accepted"]=bool(train.execute_remote_command(unreal.LBPressTrainACommand.POWER_ON,source,AUTH));checks[f"train_{letter}_start_accepted"]=bool(train.execute_remote_command(unreal.LBPressTrainACommand.START,source,AUTH))
  if not all(checks.values()):finish();return
  state="cycling";return
 if state=="cycling":
  for letter,train in trains.items():
   data=rest[letter];motion[letter]["destack"]=max([motion[letter]["destack"]]+[dist(a.get_actor_location(),p) for a,p in data["destack"]])
   deltas=[dist(a.get_actor_location(),p) for a,p in data["transfer"]]
   if deltas:motion[letter]["transfer"]=max(motion[letter]["transfer"],min(deltas))
   if data["roles"]["unload"]:motion[letter]["unload"]=max(motion[letter]["unload"],adelta(data["roles"]["unload"][0].get_actor_rotation().yaw,data["unload"]))
   if train.get_hmi_status().cycle_progress>.985:completed.add(letter)
  if len(completed)==4:finish()
handle=unreal.register_slate_post_tick_callback(tick)
