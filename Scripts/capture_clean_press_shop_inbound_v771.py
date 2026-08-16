"""Transient visual receipts for the clean-map inbound installation."""
from pathlib import Path
from datetime import datetime, timezone
import json
import time
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_Trains_InboundVisual_v770"
ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/clean_inbound_v771"
AUDIT = ROOT / "Saved/Audits/PressShopIntegration/clean_inbound_capture_v771.json"
VIEWS = [
    ("inbound_lorry_unloading.png", unreal.Vector(-18000, 4200, 2450), unreal.Vector(-13300,-2000,250), 67.0),
    ("inbound_crane_handoff.png", unreal.Vector(-10300,1200,1450), unreal.Vector(-12250,-2000,330), 58.0),
    ("inbound_to_press_trains.png", unreal.Vector(-7200,-9400,3800), unreal.Vector(-2000,-1000,350), 70.0),
]
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
OUT.mkdir(parents=True, exist_ok=True)
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.SystemLibrary.execute_console_command(world, "r.ExposureOffset 2.0")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
cams=[]
for _, loc, target, fov in VIEWS:
    cam=actors.spawn_actor_from_class(unreal.CameraActor, loc, unreal.Rotator())
    cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(loc,target),False)
    cam.camera_component.set_editor_property("field_of_view",fov)
    cams.append(cam)
i=0; task=None; started=0.0; handle=None; records=[]
def begin():
    global task, started
    path=OUT/VIEWS[i][0]
    if path.exists(): path.unlink()
    task=unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,str(path),camera=cams[i],mask_enabled=False,capture_hdr=False,delay=0,force_game_view=True)
    started=time.monotonic()
def tick(_):
    global i, handle
    path=OUT/VIEWS[i][0]
    if not(path.exists() and path.stat().st_size>1024) and time.monotonic()-started<90: return
    ok=path.exists() and path.stat().st_size>1024
    records.append({"file":str(path),"bytes":path.stat().st_size if path.exists() else 0,"status":"CAPTURE_PASS" if ok else "CAPTURE_FAIL"})
    i+=1
    if i<len(VIEWS): begin(); return
    if handle: unreal.unregister_slate_post_tick_callback(handle); handle=None
    AUDIT.parent.mkdir(parents=True,exist_ok=True)
    AUDIT.write_text(json.dumps({"revision":"v771","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"FRESH_CLEAN_INBOUND_VISUAL_RECEIPTS","map":MAP,"captures":records,"map_saved":False,"meshy_credits_used":0},indent=2),encoding="utf-8")
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()
begin(); handle=unreal.register_slate_post_tick_callback(tick)
