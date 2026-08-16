from pathlib import Path
from datetime import datetime, timezone
import json
import time
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_CleanInboundRuntimeNavFleetFix_v20260809_v049"
ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/clean_support_fleet_v20260809_v051/support_fleet_south.png"
AUDIT = ROOT / "Saved/Audits/PressShopIntegration/clean_support_fleet_capture_v20260809_v051.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError("load failed")
OUT.parent.mkdir(parents=True, exist_ok=True)
if OUT.exists(): OUT.unlink()
world = unreal.EditorLevelLibrary.get_editor_world()
for actor in actors.get_all_level_actors():
    if "roof" in actor.get_actor_label().lower() or "ceiling" in actor.get_actor_label().lower():
        actor.set_actor_hidden_in_game(True)
loc = unreal.Vector(-200, -5000, 1450)
target = unreal.Vector(-250, -4050, 120)
cam = actors.spawn_actor_from_class(unreal.CameraActor, loc, unreal.Rotator())
cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(loc, target), False)
cam.camera_component.set_editor_property("field_of_view", 72.0)
unreal.SystemLibrary.execute_console_command(world, "viewmode unlit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,str(OUT),camera=cam,mask_enabled=False,capture_hdr=False,delay=0,force_game_view=True)
if not task.is_valid_task(): raise RuntimeError("invalid screenshot task")
started=time.monotonic(); handle=None
def tick(_):
    global handle
    if not (OUT.exists() and OUT.stat().st_size > 1024) and time.monotonic()-started < 90: return
    ok=OUT.exists() and OUT.stat().st_size > 1024
    if handle: unreal.unregister_slate_post_tick_callback(handle); handle=None
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps({"generated_utc":datetime.now(timezone.utc).isoformat(),"status":"CAPTURE_PASS__VISUAL_REVIEW_REQUIRED" if ok else "CAPTURE_FAIL","map":MAP,"file":str(OUT),"bytes":OUT.stat().st_size if OUT.exists() else 0,"meshy_credits_used":0},indent=2),encoding="utf-8")
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()
handle=unreal.register_slate_post_tick_callback(tick)
