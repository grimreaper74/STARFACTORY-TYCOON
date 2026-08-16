"""Sequential four-unit commission, dispatch and exact return proof for clean v052."""
from pathlib import Path
from datetime import datetime, timezone
import json,time,unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT=Path(unreal.Paths.project_dir()); MAP="/Game/LineBoss/Maps/LB_PressShop_CleanInboundSupportFleetDockContactFix_v20260809_v069"; OUT=ROOT/"Saved/Audits/PressShopIntegration/clean_support_fleet_dock_contact_runtime_pie_v20260809_v070.json"
UNITS=("LB-CR01-01","LB-CR01-02","LB-MR01-01","LB-MR01-02")
ROOTS={"LB-CR01-01":(-750,-4050,56),"LB-CR01-02":(-250,-4050,56),"LB-MR01-01":(250,-4050,71.575),"LB-MR01-02":(-1250,-4050,71.575)}
STANDBY=(0,-3500)
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP): raise RuntimeError("load failed")
OUT.parent.mkdir(parents=True,exist_ok=True); unreal.EditorLevelLibrary.editor_play_simulate()
started=time.monotonic(); phase_started=started; phase="initialise"; index=0; initial=[]; cycles=[]; handle=None
def uid(r): return str(r.capture_common_save_state().unit_id)
def loc(r):
 p=r.get_actor_location(); return [round(p.x,3),round(p.y,3),round(p.z,3)]
def error(r,p):
 q=r.get_actor_location(); return ((q.x-p[0])**2+(q.y-p[1])**2)**0.5
def finish(failures):
 global handle
 if handle: unreal.unregister_slate_post_tick_callback(handle); handle=None
 OUT.write_text(json.dumps({"status":"PASS__FOUR_CLEAN_UNITS_COMMISSIONED_DISPATCHED_AND_RETURNED__NOT_PROMOTED" if not failures else "FAIL__CLEAN_SUPPORT_FLEET_RUNTIME__NOT_PROMOTED","generated_utc":datetime.now(timezone.utc).isoformat(),"map":MAP,"initial_fleet":initial,"route_cycles":cycles,"failures":failures,"runtime_time_dilation_for_test_only":10.0,"meshy_credits_used":0,"promotion_authorized":False},indent=2),encoding="utf-8")
 unreal.EditorLevelLibrary.editor_end_play(); unreal.EditorPythonScripting.set_keep_python_script_alive(False); unreal.SystemLibrary.quit_editor()
def tick(_):
 global phase_started,phase,index,initial
 now=time.monotonic()
 if now-started>180: finish([f"timeout phase={phase} index={index}"]); return
 world=unreal.EditorLevelLibrary.get_game_world()
 if not world:return
 controllers=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.LBPressShopSupportFleetController)
 maintenance=list(unreal.GameplayStatics.get_all_actors_of_class(world,unreal.LBMaintenanceAMR))
 cleaning=list(unreal.GameplayStatics.get_all_actors_of_class(world,unreal.LBCleaningAMR))
 robots=maintenance+cleaning
 by={uid(r):r for r in robots}
 if phase=="initialise":
  if len(controllers)!=1 or len(by)!=4 or not controllers[0].is_fleet_ready():
   if now-phase_started>15:finish([f"initialise failed controllers={len(controllers)} maintenance={len(maintenance)} cleaning={len(cleaning)} unique_robots={len(by)}"])
   return
  for name in UNITS:
   s=by[name].capture_common_save_state(); initial.append({"unit_id":name,"certified":bool(s.certified),"route_revalidation_required":bool(s.route_revalidation_required),"docked":bool(s.docked),"dock_id":str(s.dock_id),"automatic_return":bool(by[name].has_automatic_charging_route()),"location_cm":loc(by[name])})
  bad=[r["unit_id"] for r in initial if not(r["certified"] and not r["route_revalidation_required"] and r["docked"] and r["automatic_return"])]
  if bad:finish(["commission invariants failed "+str(bad)]);return
  unreal.SystemLibrary.execute_console_command(world,"slomo 10");phase="dispatch";phase_started=now;return
 name=UNITS[index];robot=by[name];controller=controllers[0]
 if phase=="dispatch":
  if not controller.dispatch_unit(unreal.Name(name)):finish([name+" dispatch refused"]);return
  cycles.append({"unit_id":name,"dispatch_start_cm":loc(robot)});phase="wait_standby";phase_started=now;return
 if phase=="wait_standby":
  s=robot.capture_common_save_state()
  if robot.has_route_authority():
   if now-phase_started>35:finish([name+" outbound timeout at "+str(loc(robot))])
   return
  if "NONE" not in str(s.active_fault).upper():finish([name+" outbound fault "+str(s.active_fault)+" detail="+str(robot.get_last_common_fault_detail())]);return
  e=error(robot,STANDBY);cycles[-1]["standby_cm"]=loc(robot);cycles[-1]["standby_error_cm"]=round(e,3)
  if e>15:finish([f"{name} standby error {e:.3f}"]);return
  if not controller.return_unit_to_dock(unreal.Name(name)):finish([name+" return refused"]);return
  phase="wait_return";phase_started=now;return
 if phase=="wait_return":
  s=robot.capture_common_save_state()
  if robot.has_route_authority() or not bool(s.docked):
   if now-phase_started>35:finish([name+" return timeout at "+str(loc(robot))])
   return
  e=error(robot,ROOTS[name]);cycles[-1].update({"return_cm":loc(robot),"return_error_cm":round(e,3),"dock_id":str(s.dock_id),"mission_count":int(s.mission_count)})
  if e>15:finish([f"{name} return error {e:.3f}"]);return
  index+=1
  if index==len(UNITS):finish([]);return
  phase="dispatch";phase_started=now
handle=unreal.register_slate_post_tick_callback(tick)
