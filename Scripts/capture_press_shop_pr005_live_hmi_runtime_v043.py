"""Capture fixed v043 PR-005 evidence after the real native handoff transaction."""

import os
import time
from pathlib import Path

import unreal


# This capture advances a real PIE handoff over several ticks before requesting
# its latent screenshot.  UE 5.8 otherwise auto-closes one tick after the
# top-level ExecutePythonScript returns.
unreal.EditorPythonScripting.set_keep_python_script_alive(True)


CANDIDATE = os.environ.get("LB_PR005_CAPTURE_CANDIDATE", "v043").lower()
MAPS = {
    "v043": "/Game/LineBoss/Maps/LB_PressShop_PR005LiveHMICandidate_v043",
    "v044": "/Game/LineBoss/Maps/LB_PressShop_PR005MaterialCandidate_v044",
    "v045": "/Game/LineBoss/Maps/LB_PressShop_PR005CoilFinishCandidate_v045",
    "v046": "/Game/LineBoss/Maps/LB_PressShop_PR005FloorRoutesCandidate_v046",
    "v047": "/Game/LineBoss/Maps/LB_PressShop_PR005DimensionedRoutesCandidate_v047",
    "v048": "/Game/LineBoss/Maps/LB_PressShop_PR005CADFloorCandidate_v048",
    "v049": "/Game/LineBoss/Maps/LB_PressShop_PR005FloorJunctionCandidate_v049",
    "v050": "/Game/LineBoss/Maps/LB_PressShop_PR005ServiceRoutingCandidate_v050",
    "v051": "/Game/LineBoss/Maps/LB_PressShop_PR005ServiceCoversCandidate_v051",
    "v052": "/Game/LineBoss/Maps/LB_PressShop_PR005ServiceIdentityCandidate_v052",
    "v053": "/Game/LineBoss/Maps/LB_PressShop_PR005LogisticsCandidate_v053",
    "v054": "/Game/LineBoss/Maps/LB_PressShop_PR006LevellerCandidate_v054",
    "v055": "/Game/LineBoss/Maps/LB_PressShop_PR007WasherLubeCandidate_v055",
    "v056": "/Game/LineBoss/Maps/LB_PressShop_PR007StripGuardHMICandidate_v056",
    "v057": "/Game/LineBoss/Maps/LB_PressShop_PR007RuntimeCandidate_v057",
    "v058": "/Game/LineBoss/Maps/LB_PressShop_PR008ServoBlankingCandidate_v058",
    "v059": "/Game/LineBoss/Maps/LB_PressShop_PR008TransitionGuardCandidate_v059",
    "v060": "/Game/LineBoss/Maps/LB_PressShop_PR008RuntimeCandidate_v060",
    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",
}
if CANDIDATE not in MAPS:
    raise RuntimeError(f"Unknown LB_PR005_CAPTURE_CANDIDATE={CANDIDATE!r}")
MAP = MAPS[CANDIDATE]
MODE = os.environ.get("LB_PR005_V043_CAPTURE", "live_hmi").lower()
VIEWS = {
    "live_hmi": ("LB_PR005_V043_CAM_LiveHMI", "press_shop_v043_pr005_live_hmi_runtime.png"),
    "loaded_cell": ("LB_PR005_V043_CAM_LoadedCell", "press_shop_v043_pr005_loaded_cell_runtime.png"),
    "loading_motion": ("LB_PR005_V043_CAM_LoadingMotion", "press_shop_v043_pr005_loading_motion_runtime.png"),
    "coil_close": ("LB_PR005_V045_CAM_CoilLayerClose", "press_shop_v043_pr005_coil_close_runtime.png"),
    "coil_inspection": ("LB_PR005_V045_CAM_CoilLayerInspection", "press_shop_v043_pr005_coil_inspection_runtime.png"),
    "whole_line": ("LB_PR005_V046_CAM_PR005WholeLine", "press_shop_v043_pr005_whole_line_runtime.png"),
    "floor_routes": ("LB_PR005_V046_CAM_PR005FloorRoutes", "press_shop_v043_pr005_floor_routes_runtime.png"),
    "dimensioned_routes": ("LB_PR005_V047_CAM_DimensionedRoutes", "press_shop_v043_pr005_dimensioned_routes_runtime.png"),
    "routes_top": ("LB_PR005_V047_CAM_RoutesTop", "press_shop_v043_pr005_routes_top_runtime.png"),
    "cad_routes_player": ("LB_PR005_V048_CAM_CADRoutesPlayer", "press_shop_v043_pr005_cad_routes_player_runtime.png"),
    "cad_routes_plan": ("LB_PR005_V048_CAM_CADRoutesPlan", "press_shop_v043_pr005_cad_routes_plan_runtime.png"),
    "cad_routes_whole_line": ("LB_PR005_V048_CAM_CADRoutesWholeLine", "press_shop_v043_pr005_cad_routes_whole_line_runtime.png"),
    "junction_player": ("LB_PR005_V049_CAM_JunctionPlayer", "press_shop_v043_pr005_junction_player_runtime.png"),
    "junction_elevated": ("LB_PR005_V049_CAM_JunctionElevated", "press_shop_v043_pr005_junction_elevated_runtime.png"),
    "junction_whole_line": ("LB_PR005_V049_CAM_JunctionWholeLine", "press_shop_v043_pr005_junction_whole_line_runtime.png"),
    "service_routing_player": ("LB_PR005_V050_CAM_ServiceRoutingPlayer", "press_shop_v043_pr005_service_routing_player_runtime.png"),
    "service_routing_elevated": ("LB_PR005_V050_CAM_ServiceRoutingElevated", "press_shop_v043_pr005_service_routing_elevated_runtime.png"),
    "service_routing_whole_line": ("LB_PR005_V050_CAM_ServiceRoutingWholeLine", "press_shop_v043_pr005_service_routing_whole_line_runtime.png"),
    "service_covers_player": ("LB_PR005_V051_CAM_ServiceCoversPlayer", "press_shop_v043_pr005_service_covers_player_runtime.png"),
    "service_covers_elevated": ("LB_PR005_V051_CAM_ServiceCoversElevated", "press_shop_v043_pr005_service_covers_elevated_runtime.png"),
    "service_covers_whole_line": ("LB_PR005_V051_CAM_ServiceCoversWholeLine", "press_shop_v043_pr005_service_covers_whole_line_runtime.png"),
    "service_identity_player": ("LB_PR005_V052_CAM_ServiceIdentityPlayer", "press_shop_v043_pr005_service_identity_player_runtime.png"),
    "service_identity_elevated": ("LB_PR005_V052_CAM_ServiceIdentityElevated", "press_shop_v043_pr005_service_identity_elevated_runtime.png"),
    "service_identity_whole_line": ("LB_PR005_V052_CAM_ServiceIdentityWholeLine", "press_shop_v043_pr005_service_identity_whole_line_runtime.png"),
    "logistics_player": ("LB_PR005_V053_CAM_LogisticsPlayer", "press_shop_v043_pr005_logistics_player_runtime.png"),
    "logistics_elevated": ("LB_PR005_V053_CAM_LogisticsElevated", "press_shop_v043_pr005_logistics_elevated_runtime.png"),
    "logistics_whole_line": ("LB_PR005_V053_CAM_LogisticsWholeLine", "press_shop_v043_pr005_logistics_whole_line_runtime.png"),
    "pr006_operator": ("LB_PR006_V054_CAM_Operator", "press_shop_v054_pr006_operator_runtime.png"),
    "pr006_drive": ("LB_PR006_V054_CAM_Drive", "press_shop_v054_pr006_drive_runtime.png"),
    "pr006_front_end": ("LB_PR006_V054_CAM_FrontEnd", "press_shop_v054_pr006_front_end_runtime.png"),
    "pr007_operator": ("LB_PR007_V055_CAM_Operator", "press_shop_v055_pr007_operator_runtime.png"),
    "pr007_service": ("LB_PR007_V055_CAM_Service", "press_shop_v055_pr007_service_runtime.png"),
    "pr007_connected_line": ("LB_PR007_V055_CAM_ConnectedLine", "press_shop_v055_pr007_connected_line_runtime.png"),
    "pr007_connected_strip": ("LB_PR007_V056_CAM_ConnectedStrip", "press_shop_v056_pr007_connected_strip_runtime.png"),
    "pr007_guard_hmi": ("LB_PR007_V056_CAM_OperatorGuardHMI", "press_shop_v056_pr007_guard_hmi_runtime.png"),
    "pr007_elevated_line": ("LB_PR007_V056_CAM_ElevatedLine", "press_shop_v056_pr007_elevated_line_runtime.png"),
    "pr007_runtime_operator": ("LB_PR007_V056_CAM_OperatorGuardHMI", "press_shop_v057_pr007_runtime_operator.png"),
    "pr007_runtime_connected": ("LB_PR007_V056_CAM_ConnectedStrip", "press_shop_v057_pr007_runtime_connected.png"),
    "pr007_runtime_elevated": ("LB_PR007_V056_CAM_ElevatedLine", "press_shop_v057_pr007_runtime_elevated.png"),
    "pr007_runtime_hmi_close": ("LB_PR007_V057_CAM_RuntimeHMI", "press_shop_v057_pr007_runtime_hmi_close.png"),
    "pr007_runtime_service_motion": ("LB_PR007_V057_CAM_RuntimeServiceMotion", "press_shop_v057_pr007_runtime_service_motion.png"),
    "pr008_operator": ("LB_PR008_V058_CAM_Operator", "press_shop_v058_pr008_operator_runtime.png"),
    "pr008_drive": ("LB_PR008_V058_CAM_Drive", "press_shop_v058_pr008_drive_runtime.png"),
    "pr008_connected_line": ("LB_PR008_V058_CAM_ConnectedLine", "press_shop_v058_pr008_connected_line_runtime.png"),
    "pr008_transition_operator": ("LB_PR008_V059_CAM_TransitionOperator", "press_shop_v059_pr008_transition_operator_runtime.png"),
    "pr008_transition_elevated": ("LB_PR008_V059_CAM_TransitionElevated", "press_shop_v059_pr008_transition_elevated_runtime.png"),
    "pr008_transition_connected": ("LB_PR008_V059_CAM_ConnectedLine", "press_shop_v059_pr008_transition_connected_runtime.png"),
    "pr008_runtime_hmi": ("LB_PR008_V060_CAM_RuntimeHMI", "press_shop_v060_pr008_runtime_hmi.png"),
    "pr008_runtime_process": ("LB_PR008_V060_CAM_RuntimeProcess", "press_shop_v060_pr008_runtime_process.png"),
    "pr008_runtime_connected": ("LB_PR008_V059_CAM_ConnectedLine", "press_shop_v060_pr008_runtime_connected.png"),
    "pr006_runtime_hmi": ("LB_PR006_V061_CAM_RuntimeHMI", "press_shop_v061_pr006_runtime_hmi.png"),
    "pr006_runtime_process": ("LB_PR006_V061_CAM_RuntimeProcess", "press_shop_v061_pr006_runtime_process.png"),
    "pr006_runtime_connected": ("LB_PR008_V059_CAM_ConnectedLine", "press_shop_v061_pr006_runtime_connected.png"),
}
if MODE not in VIEWS:
    raise RuntimeError(f"Unknown LB_PR005_V043_CAPTURE={MODE!r}")
CAMERA_LABEL, FILENAME = VIEWS[MODE]
FILENAME = FILENAME.replace("v043", CANDIDATE)
OUTPUT = Path(unreal.Paths.project_saved_dir()) / f"ValidationScreenshots/PressShopIntegration/{CANDIDATE}_pr005_runtime" / FILENAME
CAMERA_TAG = unreal.Name(f"LB.Capture.PR005.{CANDIDATE}.{MODE}")
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
capture_camera.set_actor_label(f"LB_PR005_{CANDIDATE.upper()}_CAPTURE_{MODE.upper()}")
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
transferred_done = False


def fail(reason):
    global handle
    unreal.log_error(f"LINE_BOSS_PR005_{CANDIDATE.upper()}_CAPTURE_FAIL mode={MODE} reason={reason}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def finish_tick(_delta_seconds):
    global handle
    if OUTPUT.exists() and OUTPUT.stat().st_size >= 1024:
        unreal.log(f"LINE_BOSS_PR005_{CANDIDATE.upper()}_CAPTURE_PASS mode={MODE} output={OUTPUT}")
    elif time.monotonic() - capture_started_at < 80.0:
        return
    else:
        fail("screenshot_timeout")
        return
    unreal.unregister_slate_post_tick_callback(handle)
    handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def tick(_delta_seconds):
    global handle, capture_started_at, prepared, transferred_done
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
            pr004.unpackage_coil(unreal.Name("V043_CAPTURE_UNPACKAGE")),
            pr005.select_recipe(unreal.Name("U_SERIES_1500"), 1500.0),
        ]
        if not all(steps):
            fail(f"handoff_setup={steps}")
            return
        prepared = True
        return

    if not transferred_done:
        blockers = flow.can_transfer_ready_coil(1500.0)
        transferred = blockers is not None and flow.transfer_ready_coil_to_pr005(
            unreal.Name(f"TX-PR004-PR005-{CANDIDATE.upper()}-CAPTURE"), 1500.0)
        if not transferred or pr005.get_current_traceability_barcode() != BARCODE:
            fail(f"handoff_transaction={transferred} blockers={blockers}")
            return
        transferred_done = True
        return

    if CANDIDATE in ("v057", "v058", "v059", "v060", "v061"):
        pr007_rows = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPR007Station)
        if len(pr007_rows) != 1:
            return
        if "RUNNING" not in str(pr007_rows[0].get_hmi_status().state).upper():
            return

    if CANDIDATE in ("v060", "v061"):
        pr008_rows = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPR008Station)
        if len(pr008_rows) != 1:
            return
        pr008_status = pr008_rows[0].get_hmi_status()
        if "RUNNING" not in str(pr008_status.state).upper() or pr008_status.blanks_produced < 1:
            return

    if CANDIDATE == "v061":
        pr006_rows = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPR006Station)
        if len(pr006_rows) != 1:
            return
        pr006_status = pr006_rows[0].get_hmi_status()
        if "RUNNING" not in str(pr006_status.state).upper() or pr006_status.strip_travel_metres < 0.5:
            return

    if MODE == "loading_motion":
        progress = pr005.get_coil_loading_presentation_progress()
        if progress < 0.12:
            return
        if progress > 0.45:
            fail(f"loading_motion_capture_window_missed progress={progress}")
            return
    elif MODE in ("loaded_cell", "coil_close", "coil_inspection", "whole_line", "floor_routes", "dimensioned_routes", "routes_top", "cad_routes_player", "cad_routes_plan", "cad_routes_whole_line", "junction_player", "junction_elevated", "junction_whole_line", "service_routing_player", "service_routing_elevated", "service_routing_whole_line", "service_covers_player", "service_covers_elevated", "service_covers_whole_line", "service_identity_player", "service_identity_elevated", "service_identity_whole_line", "logistics_player", "logistics_elevated", "logistics_whole_line", "pr006_operator", "pr006_drive", "pr006_front_end", "pr007_operator", "pr007_service", "pr007_connected_line") and pr005.get_coil_loading_presentation_progress() < 1.0:
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
