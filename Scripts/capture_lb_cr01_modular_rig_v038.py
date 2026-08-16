"""Capture fresh fixed-camera Unreal evidence for the CR01 v038 modular rig."""
import os
import time
from pathlib import Path

import unreal

MAP = "/Game/LineBoss/Developer/Validation/LB_CR01_CleaningAMR_ModularRig_v038"
CAPTURES = {
    "oblique": ("LB_CR01_V038_CAM_Oblique", "lb_cr01_v038_oblique.png", False),
    "left": ("LB_CR01_V038_CAM_Left", "lb_cr01_v038_left.png", False),
    "right": ("LB_CR01_V038_CAM_Right", "lb_cr01_v038_right.png", False),
    "top": ("LB_CR01_V038_CAM_Top", "lb_cr01_v038_top.png", False),
    "deployed": ("LB_CR01_V038_CAM_Oblique", "lb_cr01_v038_deployed.png", True),
}

capture_id = os.environ.get("LB_CR01_CAPTURE", "oblique").lower()
camera_label, filename, deployed = CAPTURES[capture_id]
output = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/LB_CR01/Candidate_v038" / filename
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)
actors = {actor.get_actor_label(): actor for actor in actors_api.get_all_level_actors()}
camera = actors.get(camera_label)
if camera is None:
    raise RuntimeError(f"Missing {camera_label}")

if deployed:
    # Deterministic operating pose matching the animation's fully deployed state.
    for suffix, drop in (("SM_FrontBrushLift", 8.0), ("SM_ScrubDeckLift", 12.0), ("SM_SqueegeeLift", 10.0)):
        actor = actors["LB_CR01_V038_" + suffix]
        loc = actor.get_actor_location()
        actor.set_actor_location(unreal.Vector(loc.x, loc.y, loc.z - drop), False, False)
    actors["LB_CR01_V038_SM_SideBrushArm_L"].set_actor_rotation(unreal.Rotator(0.0, -65.0, 0.0), False)
    actors["LB_CR01_V038_SM_SideBrushArm_R"].set_actor_rotation(unreal.Rotator(0.0, 65.0, 0.0), False)

output.parent.mkdir(parents=True, exist_ok=True)
if output.exists():
    output.unlink()
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(
    1600, 1000, str(output), camera=camera, mask_enabled=False, capture_hdr=False,
    comparison_tolerance=unreal.ComparisonTolerance.LOW,
    comparison_notes=f"LB-CR01 v038 {capture_id}", delay=0.0, force_game_view=True,
)
if not task.is_valid_task():
    raise RuntimeError("Invalid screenshot task")

started = time.monotonic()
tick_handle = None
def finish(_delta):
    global tick_handle
    elapsed = time.monotonic() - started
    if elapsed >= 3.0 and output.exists() and output.stat().st_size >= 1024:
        unreal.log(f"LINE_BOSS_LB_CR01_V038_CAPTURE_PASS {capture_id} {output}")
    elif elapsed < 55.0:
        return
    else:
        unreal.log_error(f"LINE_BOSS_LB_CR01_V038_CAPTURE_FAIL {capture_id}")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    unreal.SystemLibrary.quit_editor()
tick_handle = unreal.register_slate_post_tick_callback(finish)
