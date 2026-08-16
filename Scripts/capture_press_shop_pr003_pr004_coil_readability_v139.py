"""Capture one isolated PR003/PR004 environment view per editor process."""

import os
import time
from pathlib import Path

import unreal


candidate = os.environ.get("LB_ENV_COIL_READABILITY_CANDIDATE", "v139").lower()
MAPS = {
    "v139": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004CoilReadabilityCandidate_v139",
    "v140": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004CoilReadabilityCandidate_v140",
    "v141": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004CoilReadabilityCandidate_v141",
    "v181": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004BalancedHallCandidate_v181",
    "v182": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004BalancedHallCandidate_v182",
    "v183": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004BalancedHallCandidate_v183",
    "v190": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004HookLightingMergeCandidate_v190",
}
if candidate not in MAPS:
    raise RuntimeError(candidate)
MAP = MAPS[candidate]
prefix = candidate.upper()
CAPTURES = {
    "coils": (f"LB_ENV_{prefix}_CAM_CoilStoreSilver", f"press_shop_{candidate}_coil_store_silver.png"),
    "agv": (f"LB_ENV_{prefix}_CAM_AGVLoadedClose", f"press_shop_{candidate}_agv_loaded_close.png"),
    "frontend": (f"LB_ENV_{prefix}_CAM_FrontEndFlow", f"press_shop_{candidate}_front_end_flow.png"),
}
if candidate == "v141":
    CAPTURES = {
        "coils": ("LB_ENV_V141_CAM_CoilStoreNorth", "press_shop_v141_coil_store_north.png"),
        "frontend": ("LB_ENV_V141_CAM_FrontEndFlow", "press_shop_v141_front_end_flow.png"),
    }
elif candidate == "v181":
    CAPTURES = {
        "frontend": ("LB_ENV_V181_CAM_FrontEndFlow", "press_shop_v181_front_end_flow.png"),
        "management": ("LB_ENV_V181_CAM_PR003PR004Management", "press_shop_v181_pr003_pr004_management.png"),
        "wall": ("LB_ENV_V181_CAM_NorthWallCell", "press_shop_v181_north_wall_cell.png"),
        "coils": ("LB_ENV_V141_CAM_CoilStoreNorth", "press_shop_v181_coil_store_north.png"),
    }
elif candidate == "v182":
    CAPTURES = {
        "frontend": ("LB_ENV_V182_CAM_FrontEndFlow", "press_shop_v182_front_end_flow.png"),
        "management": ("LB_ENV_V182_CAM_PR003PR004Management", "press_shop_v182_pr003_pr004_management.png"),
        "wall": ("LB_ENV_V182_CAM_NorthWallCell", "press_shop_v182_north_wall_cell.png"),
        "coils": ("LB_ENV_V141_CAM_CoilStoreNorth", "press_shop_v182_coil_store_north.png"),
    }
elif candidate == "v183":
    CAPTURES = {
        "frontend": ("LB_ENV_V183_CAM_FrontEndFlow", "press_shop_v183_front_end_flow.png"),
        "management": ("LB_ENV_V183_CAM_PR003PR004Management", "press_shop_v183_pr003_pr004_management.png"),
        "wall": ("LB_ENV_V183_CAM_NorthWallCell", "press_shop_v183_north_wall_cell.png"),
        "coils": ("LB_ENV_V141_CAM_CoilStoreNorth", "press_shop_v183_coil_store_north.png"),
    }
elif candidate == "v190":
    CAPTURES = {
        "hookside": ("LB_PR004_V190_CAM_PoweredCHookFullSide", "press_shop_v190_powered_chook_full_side.png"),
        "hookbore": ("LB_PR004_V190_CAM_PoweredCHookTrueBoreAxis", "press_shop_v190_powered_chook_true_bore_axis.png"),
        "hookoblique": ("LB_PR004_V190_CAM_PoweredCHookLoadArmOblique", "press_shop_v190_powered_chook_load_arm_oblique.png"),
        "coils": ("LB_ENV_V141_CAM_CoilStoreNorth", "press_shop_v190_coil_store_north.png"),
        "frontend": ("LB_ENV_V141_CAM_FrontEndFlow", "press_shop_v190_front_end_flow.png"),
    }
capture_id = os.environ.get("LB_ENV_V139_CAPTURE", "coils").lower()
if capture_id not in CAPTURES:
    raise RuntimeError(capture_id)
camera_label, filename = CAPTURES[capture_id]
folder = (f"{candidate}_pr003_pr004_balanced_hall" if candidate in ("v181", "v182", "v183")
          else (f"{candidate}_pr003_pr004_hook_lighting_merge" if candidate == "v190"
                else f"{candidate}_pr003_pr004_coil_readability"))
output = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration" / folder / filename
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
camera = next((actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == camera_label), None)
if camera is None:
    raise RuntimeError(camera_label)
output.parent.mkdir(parents=True, exist_ok=True)
if output.exists():
    output.unlink()
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 28")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(
    1920, 1080, str(output), camera=camera, mask_enabled=False, capture_hdr=False,
    comparison_tolerance=unreal.ComparisonTolerance.LOW,
    comparison_notes=f"Cairnwell PR003 coil readability {candidate}: {capture_id}",
    delay=0.0, force_game_view=True,
)
if not task.is_valid_task():
    raise RuntimeError(f"invalid screenshot task for {capture_id}")
started = time.monotonic()
handle = None


def finish(_delta):
    global handle
    elapsed = time.monotonic() - started
    if elapsed >= 3.0 and output.exists() and output.stat().st_size >= 1024:
        unreal.log(f"LB_ENV_{prefix}_CAPTURE_PASS id={capture_id} path={output}")
    elif elapsed < 55.0:
        return
    else:
        unreal.log_error(f"LB_ENV_{prefix}_CAPTURE_FAIL id={capture_id} path={output}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.SystemLibrary.quit_editor()


handle = unreal.register_slate_post_tick_callback(finish)
