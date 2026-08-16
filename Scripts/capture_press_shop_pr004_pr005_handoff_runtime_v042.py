"""Capture fixed v042 PR-004/PR-005 evidence after the real native handoff transaction."""

import os
import time
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004PR005HandoffCandidate_v042"
MODE = os.environ.get("LB_PR004_PR005_CAPTURE", "handoff_wide").lower()
VIEWS = {
    "handoff_wide": ("LB_PR004_PR005_V042_CAM_HandoffWide", "press_shop_v042_pr004_pr005_handoff_wide_runtime.png"),
    "pr005_payoff": ("LB_PR004_PR005_V042_CAM_PR005PayoffLoaded", "press_shop_v042_pr005_payoff_loaded_runtime.png"),
}
if MODE not in VIEWS:
    raise RuntimeError(f"Unknown LB_PR004_PR005_CAPTURE={MODE!r}")
CAMERA_LABEL, FILENAME = VIEWS[MODE]
OUTPUT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/v042_pr004_pr005_handoff_runtime" / FILENAME
CAMERA_TAG = unreal.Name(f"LB.Capture.PR004PR005.v042.{MODE}")
COIL_ID = "MCX-U-CS10-0001"
HEAT_ID = "HT-CW26-08417"
LOT_ID = "LOT-MCXU-260804-A"
BARCODE = "503184064100010"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
authored = next((actor for actor in actors_api.get_all_level_actors()
                 if actor.get_actor_label() == CAMERA_LABEL), None)
if authored is None:
    raise RuntimeError(f"Missing fixed camera {CAMERA_LABEL}")
capture_camera = actors_api.spawn_actor_from_class(
    unreal.CameraActor, authored.get_actor_location(), authored.get_actor_rotation())
capture_camera.set_actor_label(f"LB_PR004_PR005_V042_CAPTURE_{MODE.upper()}")
capture_camera.tags = [CAMERA_TAG]
capture_camera.camera_component.set_field_of_view(authored.camera_component.get_editor_property("field_of_view"))
capture_camera.camera_component.set_editor_property(
    "post_process_settings", authored.camera_component.get_editor_property("post_process_settings"))
capture_camera.camera_component.set_editor_property(
    "post_process_blend_weight", authored.camera_component.get_editor_property("post_process_blend_weight"))

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
if OUTPUT.exists():
    OUTPUT.unlink()
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
handle = None
capture_started_at = None
prepared = False


def fail(reason):
    global handle
    unreal.log_error(f"LINE_BOSS_PR004_PR005_V042_CAPTURE_FAIL mode={MODE} reason={reason}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.SystemLibrary.quit_editor()


def finish_tick(_delta_seconds):
    global handle
    if OUTPUT.exists() and OUTPUT.stat().st_size >= 1024:
        unreal.log(f"LINE_BOSS_PR004_PR005_V042_CAPTURE_PASS mode={MODE} output={OUTPUT}")
    elif time.monotonic() - capture_started_at < 80.0:
        return
    else:
        fail("screenshot_timeout")
        return
    unreal.unregister_slate_post_tick_callback(handle)
    handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.SystemLibrary.quit_editor()


def tick(_delta_seconds):
    global handle, capture_started_at, prepared
    if capture_started_at is not None:
        return
    if time.monotonic() - started > 40.0:
        fail("runtime_timeout")
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    pr004_rows = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPR004Station)
    pr005_rows = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPR005Station)
    flow_rows = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPressShopMaterialFlowController)
    camera_rows = unreal.GameplayStatics.get_all_actors_with_tag(world, CAMERA_TAG)
    if len(pr004_rows) != 1 or len(pr005_rows) != 1 or len(flow_rows) != 1 or len(camera_rows) != 1:
        return
    pr004, pr005, flow, camera = pr004_rows[0], pr005_rows[0], flow_rows[0], camera_rows[0]
    if not prepared:
        steps = [
            pr004.set_control_power(True), pr004.set_cell_commissioned(True),
            pr004.load_packaged_coil_with_traceability(COIL_ID, HEAT_ID, LOT_ID, BARCODE),
            pr004.select_depack_recipe(unreal.Name("PR004_DEPACK_STANDARD"), COIL_ID),
            pr004.set_cradle_locked(True), pr004.set_c_hook_withdrawn(True),
            pr004.unpackage_coil(unreal.Name("V042_CAPTURE_UNPACKAGE")),
            pr005.select_recipe(unreal.Name("U_SERIES_1500"), 1500.0),
        ]
        if not all(steps):
            fail(f"handoff_setup={steps}")
            return
        prepared = True
        return

    blockers = flow.can_transfer_ready_coil(1500.0)
    transferred = blockers is not None and flow.transfer_ready_coil_to_pr005(
        unreal.Name("TX-PR004-PR005-V042-CAPTURE"), 1500.0)
    if not transferred or pr005.get_current_traceability_barcode() != BARCODE:
        fail(
            f"handoff_transaction={transferred} blockers={blockers} "
            f"pr004_release={pr004.can_release_coil()} state={pr004.get_process_state()} "
            f"coil={pr004.get_current_coil_id()} heat={pr004.get_current_heat_id()} "
            f"pr005_accept={pr005.can_load_coil(COIL_ID, 1500.0)} "
            f"pr005_state={pr005.get_machine_state()} pr005_coil={pr005.get_current_coil_id()}")
        return

    capture_started_at = time.monotonic()
    unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
    unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
    unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 8")
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    unreal.unregister_slate_post_tick_callback(handle)
    handle = None
    task = unreal.AutomationLibrary.take_high_res_screenshot(
        1920, 1080, str(OUTPUT), camera=camera, force_game_view=True)
    if not task.is_valid_task():
        fail("invalid_screenshot_task")
        return
    handle = unreal.register_slate_post_tick_callback(finish_tick)


handle = unreal.register_slate_post_tick_callback(tick)
