"""PIE gate for the actual tagged 40 t crane transferring CS-10 to PR-004."""

import json
import os
import time
from datetime import datetime, timezone
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
    raise RuntimeError(f"Unknown LB_PR004_CRANE_CANDIDATE={CANDIDATE!r}")
MAP = MAPS[CANDIDATE]
OUT = Path(unreal.Paths.project_saved_dir()) / f"Audits/press_shop_pr004_crane_runtime_{CANDIDATE}.json"
SOURCE_TAG = unreal.Name("LB.CoilSlot.CS-10")
ATTACHMENT_TAG = unreal.Name("LB.CoilSlot.CS-10.Attachment")
COIL_ID = "MCX-U-CS10-0001"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
handle = None
started_transfer = False
controller = None
station = None
source = None
hook_actor = None
attachments = []
attachment_offsets = {}
phase_rows = []
last_phase = None
max_load_follow_error_cm = 0.0
max_attachment_follow_error_cm = 0.0
fabrication_bridge_actors = []
fabrication_trolley_actors = []
lifting_hook_actors = []
lifting_reeving_actors = []
fabrication_initial_locations = {}
fabrication_initial_bridge_x = None
fabrication_initial_trolley_y = None
fabrication_initial_hook_z = None
max_fabrication_follow_error_cm = 0.0


def phase_name(value):
    for name in (
        "IDLE", "BRIDGE_TO_PICKUP", "TROLLEY_TO_PICKUP", "LOWERING_TO_PICKUP",
        "SECURING_LOAD", "RAISING_LOAD", "BRIDGE_TO_DROP", "TROLLEY_TO_DROP",
        "LOWERING_TO_DROP", "DEPOSITING", "WITHDRAWING_HOOK", "COMPLETE", "FAULT"):
        if value == getattr(unreal.LBBridgeCranePhase, name):
            return name
    return str(value)


def finish(status, failure=None):
    global handle
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    elapsed = time.monotonic() - started
    final_phase = controller.get_phase() if controller else None
    source_hidden = bool(source.get_editor_property("hidden")) if source else None
    payload = {
        "$schema": f"line-boss/audit/press-shop-pr004-crane-runtime-{CANDIDATE}/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "map": MAP,
        "configured_coil_id": COIL_ID,
        "duration_seconds": elapsed,
        "final_phase": phase_name(final_phase) if final_phase is not None else None,
        "final_fault": str(controller.get_fault()) if controller else None,
        "station_coil_id": station.get_current_coil_id() if station else None,
        "station_state": str(station.get_process_state()) if station else None,
        "source_hidden_after_deposit": source_hidden,
        "source_attachment_count": len(attachments),
        "observer_boundary_max_load_delta_cm": max_load_follow_error_cm,
        "observer_boundary_max_attachment_delta_cm": max_attachment_follow_error_cm,
        "native_same_tick_max_load_follow_error_cm": (
            controller.get_max_load_follow_error_cm() if controller else None),
        "native_same_tick_max_attachment_follow_error_cm": (
            controller.get_max_attachment_follow_error_cm() if controller else None),
        "v031_bridge_fabrication_actor_count": len(fabrication_bridge_actors),
        "v031_trolley_service_actor_count": len(fabrication_trolley_actors),
        "v031_max_fabrication_follow_error_cm": max_fabrication_follow_error_cm,
        "v032_hook_fabrication_actor_count": len(lifting_hook_actors),
        "v032_reeving_fall_actor_count": len(lifting_reeving_actors),
        "observer_boundary_note": (
            "Slate post-tick can observe scalar and actor transforms across adjacent render boundaries; "
            "native same-tick errors are the authoritative rigid-follow gate."),
        "phase_trace": phase_rows,
        "failure": failure,
        "promotion_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if failure:
        unreal.log_error(f"LINE_BOSS_PR004_CRANE_V027_RUNTIME_FAIL failure={failure} output={OUT}")
    else:
        unreal.log(f"LINE_BOSS_PR004_CRANE_V027_RUNTIME_PASS duration={elapsed:.2f} output={OUT}")
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def tick(_delta_seconds):
    global controller, station, source, hook_actor, attachments, started_transfer, last_phase
    global max_load_follow_error_cm, max_attachment_follow_error_cm, attachment_offsets
    global fabrication_bridge_actors, fabrication_trolley_actors, lifting_hook_actors, lifting_reeving_actors
    global fabrication_initial_locations, fabrication_initial_bridge_x, fabrication_initial_trolley_y, fabrication_initial_hook_z
    global max_fabrication_follow_error_cm
    elapsed = time.monotonic() - started
    if elapsed > 75.0:
        finish("RUNTIME_CRANE_TRANSFER_TIMEOUT__NOT_PROMOTED", "timeout")
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    if controller is None:
        controllers = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBBridgeCraneController)
        stations = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPR004Station)
        sources = unreal.GameplayStatics.get_all_actors_with_tag(world, SOURCE_TAG)
        if not controllers or not stations or len(sources) != 1:
            return
        controller = controllers[0]
        station = stations[0]
        source = sources[0]
        hooks = [actor for actor in unreal.GameplayStatics.get_all_actors_with_tag(
            world, unreal.Name("LB.Animation.Pivot.CHook"))
            if unreal.Name("LB.Crane.40T") in actor.tags]
        if len(hooks) != 1:
            finish("RUNTIME_CRANE_BINDING_FAIL__NOT_PROMOTED", f"c_hooks={len(hooks)}")
            return
        hook_actor = hooks[0]
        attachments = list(unreal.GameplayStatics.get_all_actors_with_tag(world, ATTACHMENT_TAG))
        expected_attachment_count = 6 if CANDIDATE in ("v039", "v040", "v041", "v042", "v043", "v044", "v045", "v046", "v047", "v048", "v049", "v050", "v051", "v052", "v053", "v054", "v055", "v056", "v057", "v058", "v059", "v060", "v061", "v108", "v109", "v110", "v113", "v116", "v117", "v118", "v119", "v124", "v136", "v140", "v141", "v142", "v180", "v190") else 3
        if len(attachments) != expected_attachment_count:
            finish("RUNTIME_CRANE_BINDING_FAIL__NOT_PROMOTED", f"source_attachments={len(attachments)}")
            return
        source_location = source.get_actor_location()
        attachment_offsets = {
            actor.get_name(): actor.get_actor_location() - source_location for actor in attachments
        }
        if CANDIDATE in ("v031", "v032", "v033", "v034", "v035", "v036", "v037", "v038", "v039", "v040", "v041", "v042", "v043", "v044", "v045", "v046", "v047", "v048", "v049", "v050", "v051", "v052", "v053", "v054", "v055", "v056", "v057", "v058", "v059", "v060", "v061", "v108", "v109", "v110", "v113", "v116", "v117", "v118", "v119", "v124", "v136", "v140", "v141", "v142", "v180", "v190"):
            bridge_candidate = "v031" if CANDIDATE in ("v032", "v033", "v034", "v035", "v036", "v037", "v038", "v039", "v040", "v041", "v042", "v043", "v044", "v045", "v046", "v047", "v048", "v049", "v050", "v051", "v052", "v053", "v054", "v055", "v056", "v057", "v058", "v059", "v060", "v061", "v108", "v109", "v110", "v113", "v116", "v117", "v118", "v119", "v124", "v136", "v140", "v141", "v142", "v180", "v190") else CANDIDATE
            candidate_actors = unreal.GameplayStatics.get_all_actors_with_tag(
                world, unreal.Name(f"LB.Asset.Candidate.{bridge_candidate}"))
            fabrication_bridge_actors = [
                actor for actor in candidate_actors
                if unreal.Name("LB.Crane.40T") in actor.tags
                and unreal.Name("LB.Motion.CraneBridge") in actor.tags
                and unreal.Name("LB.Motion.CraneTrolley") not in actor.tags
            ]
            fabrication_trolley_actors = [
                actor for actor in candidate_actors
                if unreal.Name("LB.Crane.40T") in actor.tags
                and unreal.Name("LB.Motion.CraneTrolley") in actor.tags
            ]
            fabrication_initial_locations = {
                actor.get_name(): actor.get_actor_location()
                for actor in fabrication_bridge_actors + fabrication_trolley_actors
            }
            fabrication_initial_bridge_x = controller.get_bridge_x()
            fabrication_initial_trolley_y = controller.get_trolley_y()
            if CANDIDATE == "v032":
                lifting_actors = unreal.GameplayStatics.get_all_actors_with_tag(
                    world, unreal.Name("LB.Asset.Candidate.v032"))
                lifting_hook_actors = [actor for actor in lifting_actors
                    if (unreal.Name("LB.Motion.CHook") in actor.tags
                        or (unreal.Name("LB.Motion.Hoist") in actor.tags
                            and unreal.Name("LB.Module.HoistReeving") not in actor.tags))]
                lifting_reeving_actors = [actor for actor in lifting_actors
                    if unreal.Name("LB.Module.HoistReeving") in actor.tags]
                fabrication_initial_locations.update({
                    actor.get_name(): actor.get_actor_location()
                    for actor in lifting_hook_actors + lifting_reeving_actors
                })
                fabrication_initial_hook_z = controller.get_hook_z()
        # Unattended RenderOffscreen PIE can advance only a few frames per wall
        # second while shaders stream. Accelerate simulation time without
        # changing the controller's authored crane speeds or phase sequence.
        controller.set_editor_property("custom_time_dilation", 6.0)
    if not started_transfer:
        steps = [
            station.set_control_power(True), station.set_cell_commissioned(True),
            controller.set_control_power(True), controller.set_safety_inputs(True, True, True),
            controller.discover_and_bind(),
        ]
        if not all(steps):
            finish("RUNTIME_CRANE_START_FAIL__NOT_PROMOTED", f"authority={steps}")
            return
        if abs(controller.get_hook_z() - 820.0) > 0.2:
            finish("RUNTIME_CRANE_DATUM_FAIL__NOT_PROMOTED",
                   f"initial_hook_z={controller.get_hook_z()}")
            return
        if not controller.start_configured_transfer():
            finish("RUNTIME_CRANE_START_FAIL__NOT_PROMOTED", "start_configured_transfer=false")
            return
        started_transfer = True

    phase = controller.get_phase()
    if phase != last_phase:
        phase_rows.append({
            "phase": phase_name(phase), "time_seconds": elapsed,
            "bridge_x_cm": controller.get_bridge_x(),
            "trolley_y_cm": controller.get_trolley_y(),
            "hook_z_cm": controller.get_hook_z(),
            "carrying_coil": controller.is_carrying_coil(),
        })
        last_phase = phase

    if controller.is_carrying_coil():
        # Compare the visible load to the visible C-hook. The Slate callback can
        # observe controller scalar properties one render boundary before the
        # moved actors, whereas the released game is judged by the mechanism's
        # actual world transforms.
        hook_to_load = (unreal.Vector(0.0, 150.0, -controller.get_load_centre_below_hook_cm())
                        if CANDIDATE in ("v033", "v034", "v035", "v036", "v037", "v038", "v039", "v040", "v041", "v042", "v043", "v044", "v045", "v046", "v047", "v048", "v049", "v050", "v051", "v052", "v053", "v054", "v055", "v056", "v057", "v058", "v059", "v060", "v061", "v108", "v109", "v110", "v113", "v116", "v117", "v118", "v119", "v124", "v136", "v140", "v141", "v142", "v180", "v190") else
                        unreal.Vector(0.0, 0.0, -controller.get_load_centre_below_hook_cm()))
        expected = hook_actor.get_actor_location() + hook_to_load
        load_error = (source.get_actor_location() - expected).length()
        max_load_follow_error_cm = max(max_load_follow_error_cm, load_error)
        for actor in attachments:
            expected_attachment = source.get_actor_location() + attachment_offsets[actor.get_name()]
            error = (actor.get_actor_location() - expected_attachment).length()
            max_attachment_follow_error_cm = max(max_attachment_follow_error_cm, error)

    if fabrication_initial_bridge_x is not None:
        bridge_delta = controller.get_bridge_x() - fabrication_initial_bridge_x
        trolley_delta = controller.get_trolley_y() - fabrication_initial_trolley_y
        for actor in fabrication_bridge_actors:
            expected = fabrication_initial_locations[actor.get_name()] + unreal.Vector(bridge_delta, 0.0, 0.0)
            max_fabrication_follow_error_cm = max(
                max_fabrication_follow_error_cm,
                (actor.get_actor_location() - expected).length())
        if fabrication_initial_hook_z is not None:
            hook_delta = controller.get_hook_z() - fabrication_initial_hook_z
            for actor in lifting_hook_actors:
                expected = fabrication_initial_locations[actor.get_name()] + unreal.Vector(
                    bridge_delta, trolley_delta, hook_delta)
                max_fabrication_follow_error_cm = max(
                    max_fabrication_follow_error_cm,
                    (actor.get_actor_location() - expected).length())
        for actor in fabrication_trolley_actors:
            expected = fabrication_initial_locations[actor.get_name()] + unreal.Vector(
                bridge_delta, trolley_delta, 0.0)
            max_fabrication_follow_error_cm = max(
                max_fabrication_follow_error_cm,
                (actor.get_actor_location() - expected).length())

    if phase == unreal.LBBridgeCranePhase.FAULT:
        finish("RUNTIME_CRANE_TRANSFER_FAULT__NOT_PROMOTED", str(controller.get_fault()))
        return
    if phase != unreal.LBBridgeCranePhase.COMPLETE:
        return

    failures = []
    if controller.get_fault() != unreal.LBBridgeCraneFault.NONE:
        failures.append(f"final_fault={controller.get_fault()}")
    if station.get_current_coil_id() != COIL_ID:
        failures.append(f"station_coil={station.get_current_coil_id()}")
    if not source.get_editor_property("hidden"):
        failures.append("source_not_consumed")
    if abs(controller.get_hook_z() - 820.0) > 0.2:
        failures.append(f"hook_not_safe={controller.get_hook_z()}")
    if controller.get_max_load_follow_error_cm() > 0.1:
        failures.append(f"native_load_follow={controller.get_max_load_follow_error_cm()}")
    if controller.get_max_attachment_follow_error_cm() > 0.1:
        failures.append(f"native_attachment_follow={controller.get_max_attachment_follow_error_cm()}")
    if CANDIDATE in ("v031", "v032", "v033", "v034", "v035", "v036", "v037", "v038", "v039", "v040", "v041", "v042", "v043", "v044", "v045", "v046", "v047", "v048", "v049", "v050", "v051", "v052", "v053", "v054", "v055", "v056", "v057", "v058", "v059", "v060", "v061", "v108", "v109", "v110", "v113", "v116", "v117", "v118", "v119", "v124", "v136", "v140", "v141", "v142", "v180", "v190"):
        if len(fabrication_bridge_actors) < 40:
            failures.append(f"v031_bridge_fabrication_count={len(fabrication_bridge_actors)}")
        if len(fabrication_trolley_actors) != 2:
            failures.append(f"v031_trolley_service_count={len(fabrication_trolley_actors)}")
        if max_fabrication_follow_error_cm > 0.1:
            failures.append(f"v031_fabrication_follow={max_fabrication_follow_error_cm}")
    if CANDIDATE == "v032":
        if len(lifting_hook_actors) != 11:
            failures.append(f"v032_hook_fabrication_count={len(lifting_hook_actors)}")
        if len(lifting_reeving_actors) != 4:
            failures.append(f"v032_reeving_fall_count={len(lifting_reeving_actors)}")
    expected_phases = {
        "BRIDGE_TO_PICKUP", "TROLLEY_TO_PICKUP", "LOWERING_TO_PICKUP", "SECURING_LOAD",
        "RAISING_LOAD", "BRIDGE_TO_DROP", "TROLLEY_TO_DROP", "LOWERING_TO_DROP",
        "DEPOSITING", "WITHDRAWING_HOOK", "COMPLETE",
    }
    visited = {row["phase"] for row in phase_rows}
    missing = sorted(expected_phases - visited)
    if missing:
        failures.append(f"missing_phases={missing}")
    if failures:
        finish("RUNTIME_CRANE_TRANSFER_FAIL__NOT_PROMOTED", ";".join(failures))
    else:
        finish("RUNTIME_CRANE_TRANSFER_PASS__NOT_PROMOTED")


handle = unreal.register_slate_post_tick_callback(tick)
