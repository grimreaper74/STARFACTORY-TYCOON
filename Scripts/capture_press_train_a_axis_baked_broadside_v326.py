"""Capture one broadside face of the v326 Train A review map."""
import os
import time
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
face = os.environ.get("LB_V326_CAPTURE", "a").lower()
label = "LB_V326_CAM_BROADSIDE_A" if face == "a" else "LB_V326_CAM_BROADSIDE_B"
out = Path(unreal.Paths.project_saved_dir()) / f"ValidationScreenshots/PressShopIntegration/v326_train_a_axis_baked_broadside/v326_train_a_broadside_{face}.png"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level("/Game/LineBoss/Maps/LB_PressTrainA_AxisBakedBroadsideReviewCandidate_v326"):
    raise RuntimeError("Could not load v326 map")
cam = next((a for a in actors.get_all_level_actors() if a.get_actor_label() == label), None)
if cam is None:
    raise RuntimeError("Broadside camera missing")
out.parent.mkdir(parents=True, exist_ok=True)
if out.exists():
    raise RuntimeError(f"Refusing to overwrite {out}")
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, str(out), camera=cam, force_game_view=True, delay=15)
if not task.is_valid_task():
    raise RuntimeError("Invalid screenshot task")
started = time.monotonic()
handle = None
def done(_):
    global handle
    elapsed = time.monotonic() - started
    if elapsed >= 16 and out.exists() and out.stat().st_size >= 1024:
        unreal.log(f"LB_V326_CAPTURE_PASS path={out}")
    elif elapsed < 90:
        return
    else:
        unreal.log_error("LB_V326_CAPTURE_FAIL")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
handle = unreal.register_slate_post_tick_callback(done)
