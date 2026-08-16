"""PIE integration gate for CR-30-01's maintenance-only dispatch cycle."""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)


CANDIDATE = os.environ.get("LB_SUPPORT_CRANE_CANDIDATE", "v036").lower()
MAPS = {
    "v036": "/Game/LineBoss/Maps/LB_PressShop_PR004SupportCraneCandidate_v036",
    "v037": "/Game/LineBoss/Maps/LB_PressShop_PR004SupportHookCandidate_v037",
    "v038": "/Game/LineBoss/Maps/LB_PressShop_PR004SupportHookCandidate_v038",
    "v039": "/Game/LineBoss/Maps/LB_PressShop_PR004TraceabilityCandidate_v039",
    "v040": "/Game/LineBoss/Maps/LB_PressShop_PR004WrapFinishCandidate_v040",
    "v041": "/Game/LineBoss/Maps/LB_PressShop_PR004LuminaireCandidate_v041",
    "v042": "/Game/LineBoss/Maps/LB_PressShop_PR004PR005HandoffCandidate_v042",
    "v108": "/Game/LineBoss/Maps/LB_PressShop_PR004PackageConditionCandidate_v108",
    "v109": "/Game/LineBoss/Maps/LB_PressShop_PR004SupportHoistCandidate_v109",
    "v110": "/Game/LineBoss/Maps/LB_PressShop_PR004SupportIdentityCandidate_v110",
    "v113": "/Game/LineBoss/Maps/LB_PressShop_PR004SupportIdentityCandidate_v113",
    "v116": "/Game/LineBoss/Maps/LB_PressShop_PR004CarryContextCandidate_v116",
    "v117": "/Game/LineBoss/Maps/LB_PressShop_PR004ConcreteFloorCandidate_v117",
    "v118": "/Game/LineBoss/Maps/LB_PressShop_PR004WrapResponseCandidate_v118",
    "v119": "/Game/LineBoss/Maps/LB_PressShop_PR004HallFinishCandidate_v119",
    "v124": "/Game/LineBoss/Maps/LB_PressShop_PR003Sheet2LayoutCandidate_v124",
    "v136": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004PoweredCHookCandidate_v136",
    "v141": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004PoweredCHookCandidate_v141",
    "v142": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004PoweredCHookVisualProofCandidate_v142",
    "v180": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004CoilReadabilityCandidate_v180",
    "v190": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004HookLightingMergeCandidate_v190",
    "v140": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004CoilReadabilityCandidate_v140",
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
    raise RuntimeError(f"Unknown LB_SUPPORT_CRANE_CANDIDATE={CANDIDATE!r}")
MAP = MAPS[CANDIDATE]
OUT = Path(unreal.Paths.project_saved_dir()) / f"Audits/press_shop_pr004_support_crane_runtime_{CANDIDATE}.json"
SOURCE_TAG = unreal.Name("LB.CoilSlot.CS-10")
CRANE_30_TAG = unreal.Name("LB.Crane.30T")
CRANE_40_TAG = unreal.Name("LB.Crane.40T")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
handle = None
controller = None
source = None
initial_source_location = None
primary_actors = []
primary_initial = {}
phase_trace = []
last_phase = None
started_dispatch = False
reached_service = False
requested_return = False
service_pose = None


def phase_name(value):
    for name in (
        "PARKED", "DISPATCHING_BRIDGE", "DISPATCHING_TROLLEY",
        "LOWERING_FOR_SUPPORT", "ON_STATION", "RAISING_TO_TRAVEL",
        "RETURNING_TROLLEY", "RETURNING_BRIDGE", "COMPLETE", "FAULT",
    ):
        if value == getattr(unreal.LBSupportCranePhase, name):
            return name
    return str(value)


def finish(status, failure=None):
    global handle
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    primary_drift = 0.0
    for actor in primary_actors:
        primary_drift = max(
            primary_drift,
            (actor.get_actor_location() - primary_initial[actor.get_name()]).length())
    source_drift = (
        (source.get_actor_location() - initial_source_location).length()
        if source and initial_source_location is not None else None)
    payload = {
        "$schema": f"line-boss/audit/press-shop-pr004-support-crane-runtime-{CANDIDATE}/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "map": MAP,
        "duration_seconds": time.monotonic() - started,
        "controller_class": "/Script/LineBossCarFactory.LBSupportCraneController",
        "master_coil_authority": False,
        "initial_unpermitted_dispatch_rejected": True,
        "service_pose_cm": service_pose,
        "final_phase": phase_name(controller.get_phase()) if controller else None,
        "final_fault": str(controller.get_fault()) if controller else None,
        "final_pose_cm": ({
            "bridge_x": controller.get_bridge_x(),
            "trolley_y": controller.get_trolley_y(),
            "hook_z": controller.get_hook_z(),
        } if controller else None),
        "primary_40t_actor_count_observed": len(primary_actors),
        "primary_40t_max_drift_cm": primary_drift,
        "master_coil_source_drift_cm": source_drift,
        "master_coil_source_hidden": bool(source.get_editor_property("hidden")) if source else None,
        "phase_trace": phase_trace,
        "native_automation_report": "Saved/Automation/SupportCrane_v001/index.json",
        "failure": failure,
        "promotion_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if failure:
        unreal.log_error(f"LINE_BOSS_PR004_SUPPORT_CRANE_V036_RUNTIME_FAIL failure={failure}")
    else:
        unreal.log("LINE_BOSS_PR004_SUPPORT_CRANE_V036_RUNTIME_PASS")
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def tick(_delta_seconds):
    global controller, source, initial_source_location, primary_actors, primary_initial
    global started_dispatch, reached_service, requested_return, service_pose, last_phase

    if time.monotonic() - started > 60.0:
        finish("RUNTIME_SUPPORT_CRANE_TIMEOUT__NOT_PROMOTED", "timeout")
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    if controller is None:
        controllers = unreal.GameplayStatics.get_all_actors_of_class(
            world, unreal.LBSupportCraneController)
        sources = unreal.GameplayStatics.get_all_actors_with_tag(world, SOURCE_TAG)
        if len(controllers) != 1 or len(sources) != 1:
            return
        controller = controllers[0]
        source = sources[0]
        initial_source_location = source.get_actor_location()
        primary_actors = [
            actor for actor in unreal.GameplayStatics.get_all_actors_with_tag(world, CRANE_40_TAG)
            if any(tag in actor.tags for tag in (
                unreal.Name("LB.Motion.CraneBridge"), unreal.Name("LB.Motion.CraneTrolley"),
                unreal.Name("LB.Motion.Hoist"), unreal.Name("LB.Motion.CHook")))
        ]
        primary_initial = {actor.get_name(): actor.get_actor_location() for actor in primary_actors}
        controller.set_editor_property("custom_time_dilation", 8.0)

    if not started_dispatch:
        if not controller.discover_and_bind():
            finish("RUNTIME_SUPPORT_CRANE_BINDING_FAIL__NOT_PROMOTED", "discover_and_bind=false")
            return
        if controller.can_handle_master_coils():
            finish("RUNTIME_SUPPORT_CRANE_AUTHORITY_FAIL__NOT_PROMOTED", "master_coil_authority=true")
            return
        if controller.dispatch_to_configured_service_point():
            finish("RUNTIME_SUPPORT_CRANE_INTERLOCK_FAIL__NOT_PROMOTED", "unpermitted_dispatch_started")
            return
        if controller.get_fault() != unreal.LBSupportCraneFault.MAINTENANCE_PERMIT_MISSING:
            finish("RUNTIME_SUPPORT_CRANE_INTERLOCK_FAIL__NOT_PROMOTED", "wrong_missing_permit_fault")
            return
        steps = [
            controller.set_control_power(True),
            controller.set_safety_inputs(True, True, True, True),
            controller.set_primary_crane_clear(True),
            controller.reset_fault(f"EVID_{CANDIDATE.upper()}_PERMIT_AND_ZONE_CLEAR"),
            controller.dispatch_to_configured_service_point(),
        ]
        if not all(steps):
            finish("RUNTIME_SUPPORT_CRANE_START_FAIL__NOT_PROMOTED", f"authority={steps}")
            return
        started_dispatch = True

    phase = controller.get_phase()
    if phase != last_phase:
        phase_trace.append({
            "phase": phase_name(phase),
            "time_seconds": time.monotonic() - started,
            "bridge_x_cm": controller.get_bridge_x(),
            "trolley_y_cm": controller.get_trolley_y(),
            "hook_z_cm": controller.get_hook_z(),
        })
        last_phase = phase

    if controller.is_at_service_point() and not reached_service:
        reached_service = True
        service_pose = {
            "bridge_x": controller.get_bridge_x(),
            "trolley_y": controller.get_trolley_y(),
            "hook_z": controller.get_hook_z(),
        }
        expected = (-7600.0, -4700.0, 760.0) if CANDIDATE in ("v038", "v039", "v040", "v041", "v042", "v043", "v044", "v045", "v046", "v047", "v048", "v049", "v050", "v051", "v052", "v053", "v054", "v055", "v056", "v057", "v058", "v059", "v060", "v061", "v108", "v109", "v110", "v113", "v116", "v117", "v118", "v119", "v124", "v136", "v140", "v141", "v142", "v180", "v190") else (-7600.0, -3300.0, 760.0)
        actual = (service_pose["bridge_x"], service_pose["trolley_y"], service_pose["hook_z"])
        if any(abs(a - b) > 0.2 for a, b in zip(actual, expected)):
            finish("RUNTIME_SUPPORT_CRANE_DATUM_FAIL__NOT_PROMOTED", f"service_pose={service_pose}")
            return
        requested_return = controller.return_to_park()
        if not requested_return:
            finish("RUNTIME_SUPPORT_CRANE_RETURN_FAIL__NOT_PROMOTED", "return_to_park=false")
            return

    if reached_service and requested_return and controller.is_parked():
        final_pose = (controller.get_bridge_x(), controller.get_trolley_y(), controller.get_hook_z())
        expected = (-9100.0, -4700.0, 1010.0)
        if any(abs(a - b) > 0.2 for a, b in zip(final_pose, expected)):
            finish("RUNTIME_SUPPORT_CRANE_DATUM_FAIL__NOT_PROMOTED", f"park_pose={final_pose}")
            return
        primary_drift = max(
            ((actor.get_actor_location() - primary_initial[actor.get_name()]).length()
             for actor in primary_actors), default=0.0)
        source_drift = (source.get_actor_location() - initial_source_location).length()
        if primary_drift > 0.1 or source_drift > 0.1 or source.get_editor_property("hidden"):
            finish(
                "RUNTIME_SUPPORT_CRANE_SEPARATION_FAIL__NOT_PROMOTED",
                f"primary_drift={primary_drift} source_drift={source_drift} hidden={source.get_editor_property('hidden')}")
            return
        finish("RUNTIME_SUPPORT_CRANE_DISPATCH_RETURN_PASS__NOT_PROMOTED")


handle = unreal.register_slate_post_tick_callback(tick)
