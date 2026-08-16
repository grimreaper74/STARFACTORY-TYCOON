"""Exact PIE proof: service access both sides, protected AGV handoff remains segregated."""
from datetime import datetime,timezone
from pathlib import Path
import json,time,unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP="/Game/LineBoss/Developer/Validation/LB_PressShop_InboundNavConnectedCandidate_v586"
OUT=Path(unreal.Paths.project_saved_dir())/"Audits/PressShopIntegration/inbound_segregated_nav_pie_v588.json"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):raise RuntimeError(MAP)
OUT.parent.mkdir(parents=True,exist_ok=True);unreal.EditorLevelLibrary.editor_play_simulate()
started=time.monotonic();phase_started=started;phase="wait_world";handle=None
def vec(v):return [round(v.x,2),round(v.y,2),round(v.z,2)] if v else None
def route(world,start,end):
 a=unreal.NavigationSystemV1.project_point_to_navigation(world,unreal.Vector(*start),None,None,unreal.Vector(220,220,300));b=unreal.NavigationSystemV1.project_point_to_navigation(world,unreal.Vector(*end),None,None,unreal.Vector(220,220,300));p=unreal.NavigationSystemV1.find_path_to_location_synchronously(world,a,b) if a and b else None
 return {"projected_start_cm":vec(a),"projected_end_cm":vec(b),"path_valid":bool(p and p.is_valid()),"path_partial":p.is_partial() if p else None,"path_length_cm":round(p.get_path_length(),2) if p else None,"path_points_cm":[vec(x) for x in p.path_points] if p else []}
def finish(payload):
 global handle
 payload.update({"$schema":"cairnwell/audit/press-shop-inbound-segregated-nav-pie-v588/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"map":MAP,"promotion_authorized":False});OUT.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
 if handle is not None:unreal.unregister_slate_post_tick_callback(handle);handle=None
 unreal.EditorLevelLibrary.editor_end_play();unreal.SystemLibrary.quit_editor()
def tick(_delta):
 global phase,phase_started
 now=time.monotonic();world=unreal.EditorLevelLibrary.get_game_world()
 if now-started>210:finish({"status":"FAIL__SEGREGATED_NAV_TIMEOUT"});return
 if world is None:return
 if phase=="wait_world":
  if now-phase_started<5:return
  nav=unreal.NavigationSystemV1.get_navigation_system(world)
  for actor in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.NavMeshBoundsVolume):
   if nav:nav.on_navigation_bounds_updated(actor)
  phase="wait_navigation";phase_started=now;return
 if phase=="wait_navigation":
  if unreal.NavigationSystemV1.is_navigation_being_built_or_locked(world) and now-phase_started<180:return
  accessible={
   "LORRY_DRIVER_SAFE_EXIT":route(world,(-14900,-4200,25),(-13700,-4200,25)),
   "DOCK_SERVICE_AISLE":route(world,(-14200,-3600,25),(-11800,-3600,25)),
   "CRANE_CELL_PERIMETER":route(world,(-12300,-3800,25),(-10000,-3800,25)),
   "WEST_HANDOFF_SERVICE":route(world,(-10400,-4200,25),(-9550,-3000,25)),
   "PR003_EAST_SERVICE":route(world,(-8800,-2400,25),(-6200,-2800,25)),
  }
  protected=route(world,(-10400,-3200,25),(-6200,-2800,25))
  failures=[name for name,row in accessible.items() if not row["path_valid"] or row["path_partial"]]
  if protected["path_valid"] and not protected["path_partial"]:failures.append("PROTECTED_HANDOFF_ROUTE_NOT_SEGREGATED")
  finish({"status":"PASS__BOTH_SIDES_SERVICEABLE_AND_HANDOFF_ROUTE_SEGREGATED__NOT_PROMOTED" if not failures else "FAIL__INBOUND_SEGREGATED_NAV",
          "accessible_routes":accessible,"protected_crossing_probe":protected,"failures":failures})
handle=unreal.register_slate_post_tick_callback(tick)
