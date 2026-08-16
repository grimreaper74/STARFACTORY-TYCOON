"""PIE nav proof for the enlarged inbound receiving bay and PR-003 handoff."""
from datetime import datetime, timezone
from pathlib import Path
import json, time, unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundFunctionalCandidate_v577"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/inbound_bay_nav_pie_v580.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP): raise RuntimeError(MAP)
OUT.parent.mkdir(parents=True, exist_ok=True)
unreal.EditorLevelLibrary.editor_play_simulate()
started=time.monotonic(); phase_started=started; phase="wait_world"; handle=None

def vec(v): return [round(v.x,2),round(v.y,2),round(v.z,2)] if v else None
def route(world,start,end,extent=(220,220,300)):
    a=unreal.NavigationSystemV1.project_point_to_navigation(world,unreal.Vector(*start),None,None,unreal.Vector(*extent))
    b=unreal.NavigationSystemV1.project_point_to_navigation(world,unreal.Vector(*end),None,None,unreal.Vector(*extent))
    path=unreal.NavigationSystemV1.find_path_to_location_synchronously(world,a,b) if a and b else None
    return {"projected_start_cm":vec(a),"projected_end_cm":vec(b),
            "path_valid":bool(path and path.is_valid()),"path_partial":path.is_partial() if path else None,
            "path_length_cm":round(path.get_path_length(),2) if path else None,
            "path_points_cm":[vec(p) for p in path.path_points] if path else []}
def finish(payload):
    global handle
    payload.update({"$schema":"cairnwell/audit/press-shop-inbound-bay-nav-pie-v580/v1",
                    "generated_utc":datetime.now(timezone.utc).isoformat(),"map":MAP,"promotion_authorized":False})
    OUT.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    if handle is not None: unreal.unregister_slate_post_tick_callback(handle);handle=None
    unreal.EditorLevelLibrary.editor_end_play();unreal.SystemLibrary.quit_editor()
def tick(_delta):
    global phase,phase_started
    now=time.monotonic(); world=unreal.EditorLevelLibrary.get_game_world()
    if now-started>210: finish({"status":"FAIL__INBOUND_BAY_NAV_TIMEOUT","phase":phase});return
    if world is None:return
    if phase=="wait_world":
        if now-phase_started<5:return
        nav=unreal.NavigationSystemV1.get_navigation_system(world)
        for actor in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.NavMeshBoundsVolume):
            if nav: nav.on_navigation_bounds_updated(actor)
        phase="wait_navigation";phase_started=now;return
    if phase=="wait_navigation":
        if unreal.NavigationSystemV1.is_navigation_being_built_or_locked(world) and now-phase_started<180:return
        tests={
            "LORRY_DRIVER_SAFE_EXIT":((-14900,-4200,25),(-13700,-4200,25)),
            "DOCK_SERVICE_AISLE":((-14200,-3600,25),(-11800,-3600,25)),
            "CRANE_CELL_PERIMETER":((-12300,-3800,25),(-10000,-3800,25)),
            "SADDLE_TO_PR003_SERVICE":((-10400,-3200,25),(-7800,-3200,25)),
        }
        rows={name:route(world,*points) for name,points in tests.items()}
        failures=[name for name,row in rows.items() if not row["path_valid"] or row["path_partial"]]
        finish({"status":"PASS__FOUR_INBOUND_BAY_SERVICE_ROUTES_VALID__NOT_PROMOTED" if not failures else "FAIL__INBOUND_BAY_SERVICE_ROUTES",
                "routes":rows,"failures":failures,"nav_build_elapsed_seconds":round(now-phase_started,2)})
handle=unreal.register_slate_post_tick_callback(tick)
