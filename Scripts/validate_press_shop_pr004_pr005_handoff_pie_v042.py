"""PIE gate for exact traceable PR-004 to PR-005 ownership transfer."""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)


CANDIDATE = os.environ.get("LB_PR004_PR005_HANDOFF_CANDIDATE", "v042").lower()
MAPS = {
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
    raise RuntimeError(f"Unknown LB_PR004_PR005_HANDOFF_CANDIDATE={CANDIDATE!r}")
MAP = MAPS[CANDIDATE]
OUT = Path(unreal.Paths.project_saved_dir()) / f"Audits/press_shop_pr004_pr005_handoff_runtime_{CANDIDATE}.json"
COIL_ID = "MCX-U-CS10-0001"
HEAT_ID = "HT-CW26-08417"
LOT_ID = "LOT-MCXU-260804-A"
BARCODE = "503184064100010"
TX = unreal.Name(f"TX-PR004-PR005-{CANDIDATE.upper()}-RUNTIME")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
handle = None
attempted = False
pr004 = None
pr005 = None
flow = None
payoff = None
bound_movers = []


def finish(status, failure=None):
    global handle
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    payload = {
        "$schema": f"line-boss/audit/press-shop-pr004-pr005-handoff-runtime-{CANDIDATE}/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "map": MAP,
        "duration_seconds": time.monotonic() - started,
        "transaction_id": str(TX),
        "pr004_state": str(pr004.get_process_state()) if pr004 else None,
        "pr004_coil_id": pr004.get_current_coil_id() if pr004 else None,
        "pr005_state": str(pr005.get_machine_state()) if pr005 else None,
        "pr005_coil_id": pr005.get_current_coil_id() if pr005 else None,
        "pr005_heat_id": pr005.get_current_heat_id() if pr005 else None,
        "pr005_supplier_lot_id": pr005.get_current_supplier_lot_id() if pr005 else None,
        "pr005_traceability_barcode": pr005.get_current_traceability_barcode() if pr005 else None,
        "payoff_visible_after_acceptance": (not payoff.get_editor_property("hidden")) if payoff else None,
        "native_mover_binding_count": len(bound_movers),
        "failure": failure,
        "promotion_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if failure:
        unreal.log_error(f"LINE_BOSS_PR004_PR005_{CANDIDATE.upper()}_RUNTIME_FAIL failure={failure}")
    else:
        unreal.log(f"LINE_BOSS_PR004_PR005_{CANDIDATE.upper()}_RUNTIME_PASS")
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def tick(_delta_seconds):
    global pr004, pr005, flow, payoff, bound_movers, attempted
    if time.monotonic() - started > 25.0:
        finish("RUNTIME_TRACEABLE_HANDOFF_TIMEOUT__NOT_PROMOTED", "timeout")
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    if pr004 is None:
        pr004_rows = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPR004Station)
        pr005_rows = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPR005Station)
        flow_rows = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPressShopMaterialFlowController)
        payoff_rows = unreal.GameplayStatics.get_all_actors_with_tag(
            world, unreal.Name("LB.Authority.PR005.NativeBound"))
        exact_payoff = [actor for actor in payoff_rows if "PayoffCoilTransferMover" in actor.get_actor_label()]
        if len(pr004_rows) != 1 or len(pr005_rows) != 1 or len(flow_rows) != 1 or len(exact_payoff) != 1:
            return
        pr004, pr005, flow = pr004_rows[0], pr005_rows[0], flow_rows[0]
        payoff = exact_payoff[0]
        bound_movers = list(payoff_rows)
    if attempted:
        return
    attempted = True

    steps = {
        "pr004_power": pr004.set_control_power(True),
        "pr004_commission": pr004.set_cell_commissioned(True),
        "traceable_load": pr004.load_packaged_coil_with_traceability(COIL_ID, HEAT_ID, LOT_ID, BARCODE),
        "pr004_recipe": pr004.select_depack_recipe(unreal.Name("PR004_DEPACK_STANDARD"), COIL_ID),
        "cradle_lock": pr004.set_cradle_locked(True),
        "hook_withdrawn": pr004.set_c_hook_withdrawn(True),
        "unpackage": pr004.unpackage_coil(unreal.Name(f"{CANDIDATE.upper()}_PLAYER_UNPACKAGE")),
        "pr005_recipe": pr005.select_recipe(unreal.Name("U_SERIES_1500"), 1500.0),
    }
    if not all(steps.values()):
        finish("RUNTIME_TRACEABLE_HANDOFF_SETUP_FAIL__NOT_PROMOTED", str(steps))
        return
    blockers = flow.can_transfer_ready_coil(1500.0)
    if blockers is None:
        finish("RUNTIME_TRACEABLE_HANDOFF_BLOCKED__NOT_PROMOTED", "can_transfer_ready_coil=false")
        return
    if not flow.transfer_ready_coil_to_pr005(TX, 1500.0):
        finish("RUNTIME_TRACEABLE_HANDOFF_TRANSACTION_FAIL__NOT_PROMOTED", "transfer=false")
        return

    failures = []
    if pr004.get_current_coil_id(): failures.append("pr004_still_owns_coil")
    if pr004.get_process_state() != unreal.LBPR004State.AWAITING_COIL: failures.append("pr004_not_awaiting_coil")
    if pr005.get_current_coil_id() != COIL_ID: failures.append("pr005_coil_id")
    if pr005.get_current_heat_id() != HEAT_ID: failures.append("pr005_heat_id")
    if pr005.get_current_supplier_lot_id() != LOT_ID: failures.append("pr005_supplier_lot_id")
    if pr005.get_current_traceability_barcode() != BARCODE: failures.append("pr005_barcode")
    if payoff.get_editor_property("hidden"): failures.append("payoff_presentation_hidden")
    if len(bound_movers) != 15: failures.append(f"native_mover_binding_count={len(bound_movers)}")
    finish(
        "RUNTIME_TRACEABLE_PR004_PR005_HANDOFF_PASS__NOT_PROMOTED" if not failures
        else "RUNTIME_TRACEABLE_PR004_PR005_HANDOFF_FAIL__NOT_PROMOTED",
        failures or None)


handle = unreal.register_slate_post_tick_callback(tick)
