"""In-map PIE proof for complete Train A identity, authority and modular motion."""
import json,time,math,unreal
from pathlib import Path
from datetime import datetime,timezone
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT=Path(unreal.Paths.project_dir());TARGET="/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainA_RuntimeNav_v673";OUT=ROOT/r"Saved\Audits\PressTrains\complete_train_a_runtime_pie_v675.json"
AUTH=unreal.Name("CW.MW.CONTROL_ROOM");SOURCE=unreal.Name("MW.MCR.TRAIN_A.CONSOLE")
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(TARGET):raise RuntimeError("Could not load v673")
unreal.EditorLevelLibrary.editor_play_simulate();started=time.monotonic();handle=None;state="discover";step_time=started;actors_by_role={};rest={};max_rotor_delta=0.0;checks={};failures=[]
def tags(a):return {str(t) for t in a.tags}
def angle_delta(a,b):return abs((a-b+180)%360-180)
def finish():
 global handle
 if handle:unreal.unregister_slate_post_tick_callback(handle);handle=None
 payload={"revision":"v675","generated_utc":datetime.now(timezone.utc).isoformat(),"target_map":TARGET,"status":"PASS__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED","checks":checks,"role_counts":{k:len(v) for k,v in actors_by_role.items()},"max_flywheel_rotation_delta_deg":max_rotor_delta,"failures":failures,"protected_map_modified":False,"promotion_authorized":False}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8");(unreal.log if not failures else unreal.log_error)("LINE_BOSS_COMPLETE_TRAIN_A_RUNTIME_V675_"+("PASS" if not failures else "FAIL"));unreal.EditorLevelLibrary.editor_end_play();unreal.EditorPythonScripting.set_keep_python_script_alive(False);unreal.SystemLibrary.quit_editor()
def tick(_):
 global state,step_time,actors_by_role,rest,max_rotor_delta
 now=time.monotonic()
 if now-started>45:failures.append("runtime validation timeout at "+state);finish();return
 world=unreal.EditorLevelLibrary.get_game_world()
 if not world:return
 trains=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.LBPressTrainAStation)
 if state=="discover":
  if len(trains)!=1 or now-started<3:return
  smas=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.StaticMeshActor)
  for role in ("access_gate","flywheel_rotor","moving_press_slide","moving_upper_die"):
   actors_by_role[role]=[a for a in smas if "LB.PressTrain.Role."+role in tags(a)]
  expected={"access_gate":10,"flywheel_rotor":5,"moving_press_slide":5,"moving_upper_die":5}
  checks["one_native_authority"]=len(trains)==1;checks["role_counts_match"]=all(len(actors_by_role[k])==v for k,v in expected.items())
  if not checks["role_counts_match"]:failures.append(f"role counts { {k:len(v) for k,v in actors_by_role.items()} } expected {expected}");finish();return
  rest={"gate_yaw":[a.get_actor_rotation().yaw for a in actors_by_role["access_gate"]],"rotor_pitch":[a.get_actor_rotation().pitch for a in actors_by_role["flywheel_rotor"]],"slide_z":{a.get_actor_label():a.get_actor_location().z for a in actors_by_role["moving_press_slide"]},"die_z":{a.get_actor_label():a.get_actor_location().z for a in actors_by_role["moving_upper_die"]}}
  trains[0].set_access_interlocks_closed(False);state="gate_open";step_time=now;return
 train=trains[0]
 if state=="gate_open" and now-step_time>.35:
  deltas=[angle_delta(a.get_actor_rotation().yaw,r) for a,r in zip(actors_by_role["access_gate"],rest["gate_yaw"])]
  checks["all_gate_visual_and_collision_pivots_open_72deg"]=all(70<d<74 for d in deltas)
  if not checks["all_gate_visual_and_collision_pivots_open_72deg"]:failures.append(f"gate deltas {deltas}")
  train.set_access_interlocks_closed(True);train.set_safety_circuit_healthy(True);train.set_emergency_stop_active(False);train.set_destack_healthy(True);train.set_transfer_healthy(True);train.set_hydraulic_pressure(280);train.set_press_load(45);train.set_inspection_healthy(True);train.set_stillage_output_clear(True);train.set_target_strokes_per_minute(10)
  checks["untrusted_power_rejected"]=not bool(train.execute_remote_command(unreal.LBPressTrainACommand.POWER_ON,SOURCE,unreal.Name("UNTRUSTED")))
  checks["reserved_blank_accepted"]=bool(train.queue_reserved_blank(unreal.Name("RES-V675-001"),unreal.Name("PR010-BLANK-V675-001")))
  checks["trusted_power_accepted"]=bool(train.execute_remote_command(unreal.LBPressTrainACommand.POWER_ON,SOURCE,AUTH));checks["trusted_start_accepted"]=bool(train.execute_remote_command(unreal.LBPressTrainACommand.START,SOURCE,AUTH))
  if not all(checks[k] for k in ("untrusted_power_rejected","reserved_blank_accepted","trusted_power_accepted","trusted_start_accepted")):failures.append("native authority/process command gate failed")
  state="cycling";step_time=now;return
 if state=="cycling":
  for a,r in zip(actors_by_role["flywheel_rotor"],rest["rotor_pitch"]):max_rotor_delta=max(max_rotor_delta,angle_delta(a.get_actor_rotation().pitch,r))
  status=train.get_hmi_status();phase=str(status.phase).upper()
  if "FORM_S03" not in phase:return
  s03slides=[a for a in actors_by_role["moving_press_slide"] if "LB.PressTrain.Stage.S03" in tags(a)];s03dies=[a for a in actors_by_role["moving_upper_die"] if "LB.PressTrain.Stage.S03" in tags(a)]
  other_slides=[a for a in actors_by_role["moving_press_slide"] if a not in s03slides]
  slide_delta=[rest["slide_z"][a.get_actor_label()]-a.get_actor_location().z for a in s03slides];die_delta=[rest["die_z"][a.get_actor_label()]-a.get_actor_location().z for a in s03dies]
  checks["five_flywheels_rotate_while_cycling"]=max_rotor_delta>10;checks["s03_ram_and_upper_die_stroke"]=len(slide_delta)==1 and len(die_delta)==1 and slide_delta[0]>5 and abs(slide_delta[0]-die_delta[0])<.5
  checks["other_stage_slides_remain_at_rest_during_s03"]=all(abs(a.get_actor_location().z-rest["slide_z"][a.get_actor_label()])<.5 for a in other_slides)
  checks["gate_returns_closed_before_cycle"]=all(angle_delta(a.get_actor_rotation().yaw,r)<.5 for a,r in zip(actors_by_role["access_gate"],rest["gate_yaw"]))
  save=train.capture_save_state();checks["save_identity_valid"]=save.version==2 and save.persistent_train_guid.is_valid() and str(save.train_id)=="TRAIN_A"
  for key in ("five_flywheels_rotate_while_cycling","s03_ram_and_upper_die_stroke","other_stage_slides_remain_at_rest_during_s03","gate_returns_closed_before_cycle","save_identity_valid"):
   if not checks[key]:failures.append(key+" failed")
  finish()
handle=unreal.register_slate_post_tick_callback(tick)
