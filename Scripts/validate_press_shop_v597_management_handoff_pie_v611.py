"""Exact-v597 PIE gate for standing control-room to overhead management handoff."""

from datetime import datetime, timezone
from pathlib import Path
import json
import time

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundReleaseCandidate_v597"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_v597_management_handoff_pie_v612.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
unreal.EditorLevelLibrary.editor_play_simulate()

started = time.monotonic()
phase = "wait_control_room"
phase_started = started
handle = None
evidence = {}


def controlled_pawn(controller):
    """Resolve the possessed pawn across Unreal Python API variants."""
    if hasattr(controller, "get_controlled_pawn"):
        return controller.get_controlled_pawn()
    try:
        return controller.get_editor_property("pawn")
    except Exception:
        pawns = unreal.GameplayStatics.get_all_actors_of_class(
            controller.get_world(), unreal.Pawn)
        return next((pawn for pawn in pawns if pawn.get_controller() == controller), None)


def finish(failures):
    global handle
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    payload = {
        "$schema": "cairnwell/audit/press-shop-v597-management-handoff-pie-v612/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__EXACT_V597_STANDING_OVERHEAD_RETURN_HANDOFF__NOT_PROMOTED" if not failures else "FAIL__EXACT_V597_MANAGEMENT_HANDOFF_V612__NOT_PROMOTED",
        "map": MAP,
        "evidence": evidence,
        "failures": failures,
        "promotion_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    unreal.log(f"LB_V597_MANAGEMENT_HANDOFF_{'PASS' if not failures else 'FAIL'}::{json.dumps(payload)}")
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def tick(_delta):
    global phase, phase_started
    try:
        now = time.monotonic()
        if now - started > 40.0:
            finish([f"timeout in phase {phase}"])
            return
        world = unreal.EditorLevelLibrary.get_game_world()
        if world is None:
            return
        controller = unreal.GameplayStatics.get_player_controller(world, 0)
        if controller is None:
            return

        if phase == "wait_control_room" and now - phase_started >= 4.0:
            pawn = controlled_pawn(controller)
            pawn_class = pawn.get_class().get_name() if pawn else None
            evidence["initial_pawn_class"] = pawn_class
            authorities = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPressShopBuildAuthority)
            evidence["build_authority_count"] = len(authorities)
            if pawn_class != "LBControlRoomPawn":
                finish([f"expected LBControlRoomPawn, found {pawn_class}"])
                return
            if len(authorities) != 1:
                finish([f"expected one build authority, found {len(authorities)}"])
                return
            pawn.enter_management_view()
            phase = "wait_management"
            phase_started = now
            return

        if phase == "wait_management" and now - phase_started >= 1.0:
            pawn = controlled_pawn(controller)
            pawn_class = pawn.get_class().get_name() if pawn else None
            evidence["management_pawn_class"] = pawn_class
            if pawn_class != "LBManagementPawn":
                finish([f"management handoff failed, found {pawn_class}"])
                return
            return_pawn = pawn.get_return_pawn()
            evidence["return_pawn_class"] = return_pawn.get_class().get_name() if return_pawn else None
            if return_pawn is None or return_pawn.get_class().get_name() != "LBControlRoomPawn":
                finish(["management pawn did not retain exact control-room return pawn"])
                return
            pawn.return_to_control_room()
            phase = "wait_return"
            phase_started = now
            return

        if phase == "wait_return" and now - phase_started >= 1.0:
            pawn = controlled_pawn(controller)
            pawn_class = pawn.get_class().get_name() if pawn else None
            evidence["returned_pawn_class"] = pawn_class
            management_pawns = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBManagementPawn)
            evidence["remaining_management_pawns"] = len(management_pawns)
            if pawn_class != "LBControlRoomPawn":
                finish([f"return handoff failed, found {pawn_class}"])
                return
            if management_pawns:
                finish([f"temporary management pawn was not destroyed: {len(management_pawns)}"])
                return
            finish([])
    except Exception as exc:
        finish([f"validator exception: {type(exc).__name__}: {exc}"])


handle = unreal.register_slate_post_tick_callback(tick)
