"""Exact whole-shop PIE navigation rebuild and expanded-aisle proof on v367."""
from datetime import datetime, timezone
import json
from pathlib import Path
import time
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_ExpandedTrainNavOptimizedCandidate_v367"
ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_expanded_whole_nav_pie_v368.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP): raise RuntimeError(MAP)
OUT.parent.mkdir(parents=True, exist_ok=True)
unreal.EditorLevelLibrary.editor_play_simulate()
started=time.monotonic(); phase_started=started; phase="wait_world"; handle=None

def vec(v): return [round(v.x,3),round(v.y,3),round(v.z,3)] if v else None
def route(world,start,end,extent=(175,175,250)):
    a=unreal.NavigationSystemV1.project_point_to_navigation(world,unreal.Vector(*start),None,None,unreal.Vector(*extent))
    b=unreal.NavigationSystemV1.project_point_to_navigation(world,unreal.Vector(*end),None,None,unreal.Vector(*extent))
    path=unreal.NavigationSystemV1.find_path_to_location_synchronously(world,a,b) if a and b else None
    return {"projected_start_cm":vec(a),"projected_end_cm":vec(b),"path_valid":bool(path and path.is_valid()),
            "path_partial":path.is_partial() if path else None,"path_length_cm":round(path.get_path_length(),3) if path else None,
            "path_points_cm":[vec(p) for p in path.path_points] if path else []}
def finish(payload):
    global handle
    payload.update({"$schema":"cairnwell/audit/press-shop-expanded-whole-nav-pie-v368/v1",
                    "generated_utc":datetime.now(timezone.utc).isoformat(),"map":MAP,"map_saved":False,"promotion_authorized":False})
    OUT.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    if handle is not None: unreal.unregister_slate_post_tick_callback(handle);handle=None
    unreal.EditorLevelLibrary.editor_end_play();unreal.SystemLibrary.quit_editor()
def tick(_delta):
    global phase,phase_started
    now=time.monotonic()
    if now-started>210: finish({"status":"FAIL__WHOLE_SHOP_NAV_TIMEOUT","phase":phase});return
    world=unreal.EditorLevelLibrary.get_game_world()
    if world is None:return
    if phase=="wait_world":
        if now-phase_started<5:return
        nav=unreal.NavigationSystemV1.get_navigation_system(world)
        bounds=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.NavMeshBoundsVolume)
        if nav:
            for actor in bounds:nav.on_navigation_bounds_updated(actor)
        phase="wait_navigation";phase_started=now;return
    if phase=="wait_navigation":
        if unreal.NavigationSystemV1.is_navigation_being_built_or_locked(world) and now-phase_started<180:return
        tests={
            "TRAIN_A_B":((1000,-3200,25),(6700,-3200,25)),
            "TRAIN_B_C":((1000,-1000,25),(6700,-1000,25)),
            "TRAIN_C_D":((1000,1200,25),(6700,1200,25)),
            "SUPPORT_COMMON_AISLE":((-6500,4200,25),(-300,4200,25)),
            "PR009_LOCAL":((-200,-2600,25),(1300,-2600,25)),
            "PR010_LOCAL":((850,-2800,25),(1800,-2800,25)),
        }
        rows={name:route(world,*points) for name,points in tests.items()}
        failures=[f"{name} route failed" for name,row in rows.items() if not row["path_valid"] or row["path_partial"]]
        finish({"status":"PASS__WHOLE_SHOP_NAV_REBUILD_COMPLETED_AND_SIX_ROUTES_VALID__NOT_PROMOTED" if not failures else "FAIL__WHOLE_SHOP_NAV_ROUTES",
                "nav_build_elapsed_seconds":round(now-phase_started,3),"routes":rows,"failures":failures})
handle=unreal.register_slate_post_tick_callback(tick)
