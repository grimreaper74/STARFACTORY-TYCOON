"""Capture an environment candidate in PIE after AGV authority establishes 11+1."""

import os
import time
from pathlib import Path

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
candidate = os.environ.get("LB_RUNTIME_INVENTORY_CANDIDATE", "v180").lower()
MAPS = {
    "v180": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004CoilReadabilityCandidate_v180",
    "v190": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004HookLightingMergeCandidate_v190",
    "v230": "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v230",
    "v232": "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v232",
    "v236": "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v236",
    "v239": "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v239",
    "v240": "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v240",
    "v241": "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v241",
    "v242": "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v242",
    "v249": "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v249",
}
if candidate not in MAPS:
    raise RuntimeError(candidate)
MAP = MAPS[candidate]
CAMERA_LABEL = "LB_ENV_V141_CAM_CoilStoreNorth"
OUT = Path(unreal.Paths.project_saved_dir()) / (
    f"ValidationScreenshots/PressShopIntegration/{candidate}_pr003_pr004_"
    f"{'hook_lighting_merge' if candidate == 'v190' else 'coil_readability'}/"
    f"press_shop_{candidate}_runtime_inventory_north.png")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
OUT.parent.mkdir(parents=True, exist_ok=True)
if OUT.exists():
    OUT.unlink()
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
capture_started = None
handle = None


def finish(success, detail):
    global handle
    logger = unreal.log if success else unreal.log_error
    logger(f"LB_ENV_V141_RUNTIME_INVENTORY_CAPTURE_{'PASS' if success else 'FAIL'} {detail}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.SystemLibrary.quit_editor()


def tick(_delta_seconds):
    global capture_started
    now = time.monotonic()
    if now - started > 60.0:
        finish(False, "timeout")
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    if capture_started is None:
        controllers = list(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBCoilAGVController))
        loads = list(unreal.GameplayStatics.get_all_actors_with_tag(world, unreal.Name("LB.Inventory.InTransfer")))
        stored = []
        for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
            tags = {str(tag) for tag in actor.tags}
            if ("LB.Material.PackagedCoil" in tags
                    and any(tag.startswith("LB.PR003.Layout.Slot.") for tag in tags)
                    and "LB.Inventory.InTransfer" not in tags):
                stored.append(actor)
        cameras = [
            actor for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.CameraActor)
            if actor.get_actor_label() == CAMERA_LABEL
        ]
        if len(controllers) != 1 or len(loads) != 1 or len(stored) != 11 or len(cameras) != 1:
            if now - started < 8.0:
                return
            finish(False, f"controllers={len(controllers)} loads={len(loads)} stored={len(stored)} cameras={len(cameras)}")
            return
        unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
        unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
        unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 28")
        unreal.EditorLevelLibrary.editor_set_game_view(True)
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        unreal.AutomationLibrary.finish_loading_before_screenshot()
        task = unreal.AutomationLibrary.take_high_res_screenshot(
            1920, 1080, str(OUT), camera=cameras[0], mask_enabled=False, capture_hdr=False,
            comparison_tolerance=unreal.ComparisonTolerance.LOW,
            comparison_notes=f"Cairnwell PR003 {candidate} exact runtime 11 stored + 1 transfer",
            delay=0.0, force_game_view=True,
        )
        if not task.is_valid_task():
            finish(False, "invalid screenshot task")
            return
        capture_started = now
        return
    if now - capture_started >= 3.0 and OUT.exists() and OUT.stat().st_size >= 1024:
        finish(True, f"stored=11 transfer=1 path={OUT}")
    elif now - capture_started > 50.0:
        finish(False, f"output missing path={OUT}")


handle = unreal.register_slate_post_tick_callback(tick)
