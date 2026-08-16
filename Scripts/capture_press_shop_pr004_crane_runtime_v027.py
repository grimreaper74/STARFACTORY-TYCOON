"""Capture fixed-camera evidence from the native PR-004 crane transfer in PIE.

Run one view per clean editor process with LB_PR004_CRANE_CAPTURE set to
``carry`` or ``deposit``.  The mechanism is frozen only after the requested
runtime phase is reached, so each image proves the actual native authority
rather than an editor-authored pose.
"""

import os
import time
from pathlib import Path

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)


CANDIDATE = os.environ.get("LB_PR004_CRANE_CANDIDATE", "v027").lower()
MAPS = {
    "v027": "/Game/LineBoss/Maps/LB_PressShop_PR004CraneRuntimeCandidate_v027",
    "v028": "/Game/LineBoss/Maps/LB_PressShop_PR004CraneVisualCandidate_v028",
    "v029": "/Game/LineBoss/Maps/LB_PressShop_PR004CraneLoadCandidate_v029",
    "v030": "/Game/LineBoss/Maps/LB_PressShop_PR004CraneVisualCandidate_v030",
    "v031": "/Game/LineBoss/Maps/LB_PressShop_PR004CraneFabricationCandidate_v031",
    "v032": "/Game/LineBoss/Maps/LB_PressShop_PR004CraneLiftingCandidate_v032",
    "v033": "/Game/LineBoss/Maps/LB_PressShop_PR004CraneCHookCandidate_v033",
    "v034": "/Game/LineBoss/Maps/LB_PressShop_PR004CraneManagementCandidate_v034",
    "v035": "/Game/LineBoss/Maps/LB_PressShop_PR004CraneFinishCandidate_v035",
    "v036": "/Game/LineBoss/Maps/LB_PressShop_PR004SupportCraneCandidate_v036",
    "v037": "/Game/LineBoss/Maps/LB_PressShop_PR004SupportHookCandidate_v037",
    "v038": "/Game/LineBoss/Maps/LB_PressShop_PR004SupportHookCandidate_v038",
    "v039": "/Game/LineBoss/Maps/LB_PressShop_PR004TraceabilityCandidate_v039",
    "v040": "/Game/LineBoss/Maps/LB_PressShop_PR004WrapFinishCandidate_v040",
    "v041": "/Game/LineBoss/Maps/LB_PressShop_PR004LuminaireCandidate_v041",
    "v108": "/Game/LineBoss/Maps/LB_PressShop_PR004PackageConditionCandidate_v108",
    "v113": "/Game/LineBoss/Maps/LB_PressShop_PR004SupportIdentityCandidate_v113",
    "v114": "/Game/LineBoss/Maps/LB_PressShop_PR004CarryContextCandidate_v114",
    "v115": "/Game/LineBoss/Maps/LB_PressShop_PR004CarryContextCandidate_v115",
    "v116": "/Game/LineBoss/Maps/LB_PressShop_PR004CarryContextCandidate_v116",
    "v117": "/Game/LineBoss/Maps/LB_PressShop_PR004ConcreteFloorCandidate_v117",
    "v118": "/Game/LineBoss/Maps/LB_PressShop_PR004WrapResponseCandidate_v118",
    "v119": "/Game/LineBoss/Maps/LB_PressShop_PR004HallFinishCandidate_v119",
    "v120": "/Game/LineBoss/Maps/LB_PressShop_PR004HallFinishCandidate_v120",
    "v121": "/Game/LineBoss/Maps/LB_PressShop_PR004HallFinishCandidate_v121",
    "v122": "/Game/LineBoss/Maps/LB_PressShop_PR004HallFinishCandidate_v122",
    "v123": "/Game/LineBoss/Maps/LB_PressShop_PR004HallFinishCandidate_v123",
    "v124": "/Game/LineBoss/Maps/LB_PressShop_PR003Sheet2LayoutCandidate_v124",
    "v125": "/Game/LineBoss/Maps/LB_PressShop_PR004HallFinishCandidate_v125",
    "v130": "/Game/LineBoss/Maps/LB_PressShop_PR004HallFinishCandidate_v130",
    "v131": "/Game/LineBoss/Maps/LB_PressShop_PR004HallFinishCandidate_v131",
    "v132": "/Game/LineBoss/Maps/LB_PressShop_PR004HallFinishCandidate_v132",
    "v136": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004PoweredCHookCandidate_v136",
    "v141": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004PoweredCHookCandidate_v141",
    "v142": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004PoweredCHookVisualProofCandidate_v142",
    "v143": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004PoweredCHookVisualProofCandidate_v143",
    "v190": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004HookLightingMergeCandidate_v190",
}
if CANDIDATE not in MAPS:
    raise RuntimeError(f"Unknown LB_PR004_CRANE_CANDIDATE={CANDIDATE!r}")
MAP = MAPS[CANDIDATE]
COIL_ID = "MCX-U-CS10-0001"
MODE = os.environ.get("LB_PR004_CRANE_CAPTURE", "carry").lower()
VIEWS_V027 = {
    "carry": (
        unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_INT_FRONT_CAM_CraneDetail",
        "press_shop_v027_crane_carry_runtime.png",
    ),
    "deposit": (
        unreal.LBBridgeCranePhase.COMPLETE,
        "LB_INT_PR004_V009_CAM_PR004CloseDirty",
        "press_shop_v027_crane_deposit_runtime.png",
    ),
}
VIEWS_V028 = {
    "span": (
        unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V028_CAM_CraneFullSpan",
        "press_shop_v028_crane_full_span_runtime.png",
    ),
    "span_oblique": (
        unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V028_CAM_CraneSpanOblique",
        "press_shop_v028_crane_full_span_oblique_runtime.png",
    ),
    "carry": (
        unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V028_CAM_CraneCarryWide",
        "press_shop_v028_crane_carry_wide_runtime.png",
    ),
    "carry_detail": (
        unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V028_CAM_CHookEngagement",
        "press_shop_v028_c_hook_engagement_runtime.png",
    ),
    "deposit": (
        unreal.LBBridgeCranePhase.COMPLETE,
        "LB_PR004_V028_CAM_PR004Deposit",
        "press_shop_v028_crane_deposit_runtime.png",
    ),
}
VIEWS_V029 = {
    "span_clear": (
        unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V029_CAM_CraneSpanClear",
        "press_shop_v029_crane_full_span_clear_runtime.png",
    ),
    "carry_detail": (
        unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V028_CAM_CHookEngagement",
        "press_shop_v029_c_hook_packaged_load_runtime.png",
    ),
    "deposit": (
        unreal.LBBridgeCranePhase.COMPLETE,
        "LB_PR004_V028_CAM_PR004Deposit",
        "press_shop_v029_crane_deposit_runtime.png",
    ),
}
VIEWS_V030 = {
    "span_west": (
        unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V030_CAM_CraneFullSpanWest",
        "press_shop_v030_crane_full_span_west_runtime.png",
    ),
    "carry_detail": (
        unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V028_CAM_CHookEngagement",
        "press_shop_v030_c_hook_packaged_load_runtime.png",
    ),
    "deposit": (
        unreal.LBBridgeCranePhase.COMPLETE,
        "LB_PR004_V028_CAM_PR004Deposit",
        "press_shop_v030_crane_deposit_runtime.png",
    ),
}
VIEWS_V031 = {
    "span_west": (
        unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V031_CAM_CraneFullSpanWest",
        "press_shop_v031_crane_full_span_fabricated_runtime.png",
    ),
    "carry_detail": (
        unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V031_CAM_CHookEngagement",
        "press_shop_v031_c_hook_packaged_load_runtime.png",
    ),
    "deposit": (
        unreal.LBBridgeCranePhase.COMPLETE,
        "LB_PR004_V031_CAM_PR004Deposit",
        "press_shop_v031_crane_deposit_runtime.png",
    ),
}
VIEWS_V032 = {
    "span_east": (
        unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V032_CAM_CraneFullSpanEast",
        "press_shop_v032_crane_full_span_east_runtime.png",
    ),
    "carry_detail": (
        unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V032_CAM_CHookFabrication",
        "press_shop_v032_c_hook_fabricated_load_runtime.png",
    ),
    "deposit": (
        unreal.LBBridgeCranePhase.COMPLETE,
        "LB_PR004_V032_CAM_PR004Deposit",
        "press_shop_v032_crane_deposit_runtime.png",
    ),
}
VIEWS_V033 = {
    "span_west": (unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V033_CAM_CraneFullSpanWest", "press_shop_v033_crane_full_span_west_runtime.png"),
    "carry_detail": (unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V033_CAM_CHookPurposeBuilt", "press_shop_v033_c_hook_purpose_built_runtime.png"),
    "hook_side": (unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V033_CAM_CHookSideProfile", "press_shop_v033_c_hook_side_profile_runtime.png"),
    "deposit": (unreal.LBBridgeCranePhase.COMPLETE,
        "LB_PR004_V033_CAM_PR004Deposit", "press_shop_v033_crane_deposit_runtime.png"),
}
VIEWS_V034 = {
    "span_management": (unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V034_CAM_CraneManagementSouthEast", "press_shop_v034_crane_management_southeast_runtime.png"),
    "carry_detail": (unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V034_CAM_CHookPurposeBuilt", "press_shop_v034_c_hook_purpose_built_runtime.png"),
    "hook_side": (unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V034_CAM_CHookSideProfile", "press_shop_v034_c_hook_side_profile_runtime.png"),
    "deposit": (unreal.LBBridgeCranePhase.COMPLETE,
        "LB_PR004_V034_CAM_PR004OperatorOblique", "press_shop_v034_crane_deposit_operator_oblique_runtime.png"),
}
VIEWS_V035 = {
    "span_management": (unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V035_CAM_CraneManagementSouthInterior", "press_shop_v035_crane_management_south_interior_runtime.png"),
    "span_management_alt": (unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V035_CAM_CraneManagementSouthInteriorAlt", "press_shop_v035_crane_management_south_interior_alt_runtime.png"),
    "span_management_clear": (unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V035_CAM_CraneManagementSouthInteriorClear", "press_shop_v035_crane_management_south_interior_clear_runtime.png"),
    "carry_detail": (unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V035_CAM_CHookPurposeBuilt", "press_shop_v035_c_hook_purpose_built_runtime.png"),
    "hook_side": (unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V035_CAM_CHookSideProfile", "press_shop_v035_c_hook_side_profile_runtime.png"),
    "deposit": (unreal.LBBridgeCranePhase.COMPLETE,
        "LB_PR004_V035_CAM_PR004OperatorOblique", "press_shop_v035_crane_deposit_operator_oblique_runtime.png"),
    "hmi_close": (unreal.LBBridgeCranePhase.COMPLETE,
        "LB_PR004_V035_CAM_PR004HMIAndCradle", "press_shop_v035_pr004_hmi_and_cradle_runtime.png"),
    "hmi_readable": (unreal.LBBridgeCranePhase.COMPLETE,
        "LB_PR004_V035_CAM_PR004HMIReadable", "press_shop_v035_pr004_hmi_readable_runtime.png"),
}
VIEWS_V039 = dict(VIEWS_V035)
VIEWS_V039.update({
    "trace_carry": (unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V039_CAM_TraceCarry", "press_shop_v039_traceability_carry_runtime.png"),
    "trace_deposit": (unreal.LBBridgeCranePhase.COMPLETE,
        "LB_PR004_V039_CAM_TraceDeposit", "press_shop_v039_traceability_deposit_runtime.png"),
})
VIEWS_V040 = dict(VIEWS_V039)
VIEWS_V040.update({
    "package_close": (unreal.LBBridgeCranePhase.COMPLETE,
        "LB_PR004_V040_CAM_PackageMaterialClose", "press_shop_v040_package_material_close_runtime.png"),
})
VIEWS_V108 = dict(VIEWS_V040)
VIEWS_V108.update({
    "package_close": (unreal.LBBridgeCranePhase.COMPLETE,
        "LB_PR004_V108_CAM_PackageConditionClose", "press_shop_v108_package_condition_close_runtime.png"),
    "trace_carry": (unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V039_CAM_TraceCarry", "press_shop_v108_traceability_carry_runtime.png"),
})
VIEWS_V114 = dict(VIEWS_V108)
VIEWS_V114["trace_carry"] = (
    unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
    "LB_PR004_V114_CAM_TraceCarryInstalledContext",
    "press_shop_v114_traceability_carry_installed_context_runtime.png")
VIEWS_V115 = dict(VIEWS_V108)
VIEWS_V115["trace_carry"] = (
    unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
    "LB_PR004_V115_CAM_TraceCarryInstalledContext",
    "press_shop_v115_traceability_carry_installed_context_runtime.png")
VIEWS_V116 = dict(VIEWS_V108)
VIEWS_V116["trace_carry"] = (
    unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
    "LB_PR004_V116_CAM_TraceCarryInstalledContext",
    "press_shop_v116_traceability_carry_installed_context_runtime.png")
VIEWS_V136 = {
    "powered_hook_side": (unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V136_CAM_PoweredCHookSide", "press_shop_v136_powered_chook_side_runtime.png"),
    "powered_hook_bore": (unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V136_CAM_PoweredCHookBore", "press_shop_v136_powered_chook_bore_runtime.png"),
}
VIEWS_V141 = {
    "powered_hook_side": (unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V141_CAM_PoweredCHookSide", "press_shop_v141_powered_chook_side_runtime.png"),
    "powered_hook_bore": (unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V141_CAM_PoweredCHookBore", "press_shop_v141_powered_chook_bore_runtime.png"),
}
VIEWS_V142 = {
    "powered_hook_side_support": (unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V142_CAM_PoweredCHookSideSupport", "press_shop_v142_powered_chook_side_support_runtime.png"),
    "powered_hook_bore_axis": (unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V142_CAM_PoweredCHookBoreAxis", "press_shop_v142_powered_chook_bore_axis_runtime.png"),
    "powered_hook_underside": (unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V142_CAM_PoweredCHookUnderside", "press_shop_v142_powered_chook_underside_runtime.png"),
}
VIEWS_V143 = {
    "powered_hook_full_side": (unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V143_CAM_PoweredCHookFullSide", "press_shop_v143_powered_chook_full_side_runtime.png"),
    "powered_hook_true_bore_axis": (unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V143_CAM_PoweredCHookTrueBoreAxis", "press_shop_v143_powered_chook_true_bore_axis_runtime.png"),
    "powered_hook_load_arm_oblique": (unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V143_CAM_PoweredCHookLoadArmOblique", "press_shop_v143_powered_chook_load_arm_oblique_runtime.png"),
}
VIEWS_V190 = {
    "powered_hook_full_side": (unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V190_CAM_PoweredCHookFullSide", "press_shop_v190_powered_chook_full_side_runtime.png"),
    "powered_hook_true_bore_axis": (unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V190_CAM_PoweredCHookTrueBoreAxis", "press_shop_v190_powered_chook_true_bore_axis_runtime.png"),
    "powered_hook_load_arm_oblique": (unreal.LBBridgeCranePhase.TROLLEY_TO_DROP,
        "LB_PR004_V190_CAM_PoweredCHookLoadArmOblique", "press_shop_v190_powered_chook_load_arm_oblique_runtime.png"),
}
VIEWS = (VIEWS_V190 if CANDIDATE == "v190" else VIEWS_V143 if CANDIDATE == "v143" else VIEWS_V142 if CANDIDATE == "v142" else VIEWS_V141 if CANDIDATE == "v141" else VIEWS_V136 if CANDIDATE == "v136" else VIEWS_V116 if CANDIDATE in ("v116", "v117", "v118", "v119", "v120", "v121", "v122", "v123", "v124", "v125", "v130", "v131", "v132") else VIEWS_V115 if CANDIDATE == "v115" else VIEWS_V114 if CANDIDATE == "v114" else VIEWS_V108 if CANDIDATE in ("v108", "v113") else VIEWS_V040 if CANDIDATE in ("v040", "v041") else VIEWS_V039 if CANDIDATE == "v039" else VIEWS_V035 if CANDIDATE in ("v035", "v036", "v037", "v038") else VIEWS_V034 if CANDIDATE == "v034" else VIEWS_V033 if CANDIDATE == "v033" else VIEWS_V032 if CANDIDATE == "v032" else VIEWS_V031 if CANDIDATE == "v031" else VIEWS_V030 if CANDIDATE == "v030" else VIEWS_V029 if CANDIDATE == "v029"
         else VIEWS_V028 if CANDIDATE == "v028" else VIEWS_V027)
if MODE not in VIEWS:
    raise RuntimeError(f"Unknown LB_PR004_CRANE_CAPTURE={MODE!r}")

TARGET_PHASE, CAMERA_LABEL, FILENAME = VIEWS[MODE]
if CANDIDATE in ("v036", "v037", "v038", "v039", "v040", "v041"):
    FILENAME = FILENAME.replace("v035", CANDIDATE)
if CANDIDATE == "v041":
    FILENAME = FILENAME.replace("v039", "v041").replace("v040", "v041")
if CANDIDATE == "v113":
    FILENAME = FILENAME.replace("v108", "v113")
if CANDIDATE == "v116":
    FILENAME = FILENAME.replace("v108", "v116")
if CANDIDATE == "v117":
    FILENAME = FILENAME.replace("v108", "v117").replace("v116", "v117")
if CANDIDATE == "v118":
    FILENAME = FILENAME.replace("v108", "v118").replace("v116", "v118")
if CANDIDATE == "v119":
    FILENAME = FILENAME.replace("v108", "v119").replace("v116", "v119")
if CANDIDATE == "v120":
    FILENAME = FILENAME.replace("v108", "v120").replace("v116", "v120")
if CANDIDATE == "v121":
    FILENAME = FILENAME.replace("v108", "v121").replace("v116", "v121")
if CANDIDATE == "v122":
    FILENAME = FILENAME.replace("v108", "v122").replace("v116", "v122")
if CANDIDATE == "v123":
    FILENAME = FILENAME.replace("v108", "v123").replace("v116", "v123")
if CANDIDATE == "v124":
    FILENAME = FILENAME.replace("v108", "v124").replace("v116", "v124")
if CANDIDATE == "v125":
    FILENAME = FILENAME.replace("v108", "v125").replace("v116", "v125")
if CANDIDATE == "v130":
    FILENAME = FILENAME.replace("v108", "v130").replace("v116", "v130")
if CANDIDATE == "v131":
    FILENAME = FILENAME.replace("v108", "v131").replace("v116", "v131")
if CANDIDATE == "v132":
    FILENAME = FILENAME.replace("v108", "v132").replace("v116", "v132")
OUTPUT = (
    Path(unreal.Paths.project_saved_dir())
    / f"ValidationScreenshots/PressShopIntegration/{CANDIDATE}_pr004_crane_runtime"
    / FILENAME
)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
CAMERA_TAG = unreal.Name(f"LB.Capture.PR004Crane.{CANDIDATE}.{MODE}")

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

# Mirror the authored fixed camera into a transient capture camera before PIE.
# AutomationLibrary is reliable with a camera spawned into the editor world
# and copied into PIE (the same route used by the accepted native HMI proof).
authored_camera = next(
    (actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == CAMERA_LABEL),
    None,
)
if authored_camera is None:
    raise RuntimeError(f"Missing authored fixed camera {CAMERA_LABEL}")
capture_camera = actors.spawn_actor_from_class(
    unreal.CameraActor,
    authored_camera.get_actor_location(),
    authored_camera.get_actor_rotation(),
)
capture_camera.set_actor_label(f"LB_PR004_{CANDIDATE.upper()}_CAM_{MODE.upper()}_PIE_FIXED")
capture_camera.tags = [CAMERA_TAG]
capture_camera.camera_component.set_field_of_view(
    authored_camera.camera_component.get_editor_property("field_of_view")
)
capture_camera.camera_component.set_editor_property(
    "post_process_settings",
    authored_camera.camera_component.get_editor_property("post_process_settings"),
)
capture_camera.camera_component.set_editor_property(
    "post_process_blend_weight",
    authored_camera.camera_component.get_editor_property("post_process_blend_weight"),
)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
if OUTPUT.exists():
    OUTPUT.unlink()

unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
handle = None
controller = None
station = None
capture_started = False
capture_started_at = None


def fail(message):
    global handle
    unreal.log_error(f"LINE_BOSS_PR004_CRANE_CAPTURE_FAIL candidate={CANDIDATE} mode={MODE} reason={message}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.SystemLibrary.quit_editor()


def find_camera(world):
    cameras = unreal.GameplayStatics.get_all_actors_with_tag(world, CAMERA_TAG)
    return cameras[0] if len(cameras) == 1 else None


def finish_tick(_delta_seconds):
    global handle
    elapsed = time.monotonic() - capture_started_at
    if OUTPUT.exists() and OUTPUT.stat().st_size >= 1024:
        unreal.log(
            f"LINE_BOSS_PR004_CRANE_CAPTURE_PASS candidate={CANDIDATE} mode={MODE} "
            f"phase={controller.get_phase()} output={OUTPUT}"
        )
    elif elapsed < 80.0:
        return
    else:
        fail("screenshot_timeout")
        return
    unreal.unregister_slate_post_tick_callback(handle)
    handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.SystemLibrary.quit_editor()


def tick(_delta_seconds):
    global handle, controller, station, capture_started, capture_started_at
    elapsed = time.monotonic() - started
    if elapsed > 80.0:
        fail("runtime_phase_timeout")
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    if controller is None:
        controllers = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBBridgeCraneController)
        stations = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPR004Station)
        if not controllers or not stations:
            return
        controller = controllers[0]
        station = stations[0]
        controller.set_editor_property("custom_time_dilation", 6.0)
        steps = [
            station.set_control_power(True),
            station.set_cell_commissioned(True),
            controller.set_control_power(True),
            controller.set_safety_inputs(True, True, True),
            controller.discover_and_bind(),
            controller.start_configured_transfer(),
        ]
        if not all(steps):
            fail(f"authority={steps}")
            return

    if capture_started or controller.get_phase() != TARGET_PHASE:
        return
    if (MODE.startswith("carry") or MODE.startswith("span")) and not controller.is_carrying_coil():
        fail("target_phase_without_load")
        return
    if MODE in ("deposit", "hmi_close", "hmi_readable", "trace_deposit", "package_close") and station.get_current_coil_id() != COIL_ID:
        fail(f"deposit_identity={station.get_current_coil_id()!r}")
        return

    camera = find_camera(world)
    if camera is None:
        fail(f"missing_fixed_camera={CAMERA_LABEL}")
        return

    capture_started = True
    capture_started_at = time.monotonic()
    # Keep the actor ticking because Unreal's PIE screenshot latent task needs
    # normal frame progression.  A near-zero actor dilation holds the authored
    # mechanism at the proven phase without substituting an editor pose.
    controller.set_editor_property("custom_time_dilation", 0.001)
    unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
    unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
    unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 8")
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    # AutomationLibrary pumps Slate internally while preparing the shot.  Stop
    # this callback before entering it to prevent a nested capture request.
    unreal.unregister_slate_post_tick_callback(handle)
    handle = None
    task = unreal.AutomationLibrary.take_high_res_screenshot(
        1920, 1080, str(OUTPUT), camera=camera, force_game_view=True
    )
    if not task.is_valid_task():
        fail("invalid_screenshot_task")
        return
    unreal.log(
        f"LINE_BOSS_PR004_CRANE_CAPTURE_READY candidate={CANDIDATE} mode={MODE} "
        f"phase={controller.get_phase()} camera={CAMERA_LABEL}"
    )
    handle = unreal.register_slate_post_tick_callback(finish_tick)


handle = unreal.register_slate_post_tick_callback(tick)
