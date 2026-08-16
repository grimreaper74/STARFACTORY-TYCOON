"""Actual-player live PIE proof for the isolated Paint Shop ED-coat slice.

The saved Paint map remains environment/bootstrap authority only.  This validator
adds one *unsaved* editor-world Weld actor solely so UE can duplicate it into PIE,
then configures the duplicated game-world actor to manufacture a truthful complete
BIW.  It never saves Content.  After PIE ends it removes the unsaved source actor
and requires the map file hash to remain byte-identical.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import time

import unreal


ROOT = Path(unreal.Paths.project_dir()).resolve()
MAP = "/Game/LineBoss/PaintShop/Experimental/v001/Maps/LB_PaintShop_Prototype_v001"
MAP_FILE = ROOT / "Content/LineBoss/PaintShop/Experimental/v001/Maps/LB_PaintShop_Prototype_v001.umap"
CREATE_RECEIPT = ROOT / "Saved/Audits/PaintShop/Experimental_v001/paint_shop_prototype_map_create_v001.json"
VALIDATION_RECEIPT = ROOT / "Saved/Audits/PaintShop/Experimental_v001/paint_shop_prototype_map_validation_v001.json"

EXPECTED_MAP_SHA256 = "2296FEE6FAF5AECB5B424E1E413B4324D1F9D3C4AF0172D7F83BC2440CE17069"
EXPECTED_CREATE_SHA256 = "4E65E671CB25D8615F3A775B1697E7D72C523D58FFA7481356A5BF8D5941AC09"
EXPECTED_VALIDATION_SHA256 = "B452A68FF04B89BF6D6FD43486230692C05B1338368794570174150DFC90F136"
EXPECTED_BUILDER_SHA256 = "6922346EA0BA04C8388BA808FF22D7A1FFCC932B87AA37AEBAA52D3A26645FCA"
EXPECTED_VALIDATOR_SHA256 = "5A687A004DAD249B0BD28C2F2941FD3E5A6770D20B3D3DB25CC9A3EFBDA7CD74"

STAMP = os.environ.get("LB_PAINTSHOP_VALIDATION_STAMP") or datetime.now(
    timezone.utc).strftime("%Y%m%dT%H%M%SZ")
RUN_DIR = ROOT / "Saved/Audits/PaintShop/Experimental_v001/ReleaseValidation" / STAMP
CAPTURE_DIR = ROOT / "Saved/ValidationScreenshots/PaintShop/Experimental_v001/ReleaseValidation" / STAMP
AUDIT = RUN_DIR / "live_pie_edcoat_validation_v001.json"
SCRIPT_FILE = Path(__file__).resolve()
SOURCE_TAG = unreal.Name("LB.PaintShop.Validation.WeldSource.v001")

EXPECTED_ASSET_PATHS = [
    "/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v002/Modules/SM_LB_EDLine_OpenTreatmentModule_NoRail_Start_v002.SM_LB_EDLine_OpenTreatmentModule_NoRail_Start_v002",
    "/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v002/Modules/SM_LB_EDLine_OpenTreatmentModule_NoRail_End_v002.SM_LB_EDLine_OpenTreatmentModule_NoRail_End_v002",
    "/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Process/SM_LB_EDLine_TreatmentLiquidSurface_Blockout_v001.SM_LB_EDLine_TreatmentLiquidSurface_Blockout_v001",
    "/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Carrier/SM_LB_EDLine_CarrierTrolley_Blockout_v001.SM_LB_EDLine_CarrierTrolley_Blockout_v001",
    "/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Carrier/SM_LB_EDLine_CarrierHoistCables_Blockout_v001.SM_LB_EDLine_CarrierHoistCables_Blockout_v001",
    "/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Carrier/SM_LB_EDLine_CarrierHanger_Blockout_v001.SM_LB_EDLine_CarrierHanger_Blockout_v001",
    "/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Validation/SM_LB_EDLine_ProxyBIW_Blockout_v001.SM_LB_EDLine_ProxyBIW_Blockout_v001",
    "/Engine/BasicShapes/Cube.Cube",
    "/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Materials/MI_LB_EDLine_Liquid_ED_Ecoat_v001.MI_LB_EDLine_Liquid_ED_Ecoat_v001",
]

SCREENSHOT_NAMES = (
    "01_actual_management_pawn_overview.png",
    "01_actual_management_pawn_overview_with_ui.png",
    "02_edcoat_immersing.png",
    "02_edcoat_immersing_with_ui.png",
    "03_edcoat_output_ready.png",
    "03_edcoat_output_ready_with_ui.png",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def enum_name(value) -> str:
    # UE 5.8 renders reflected enums as ``<EnumType.VALUE: integral>``.
    # Normalize that representation to the stable enumerator name only.
    text = str(value).rsplit(".", 1)[-1]
    return text.split(":", 1)[0].strip("<> ")


def name_text(value) -> str:
    return str(value)


def json_default(value):
    """Serialize the one reflected scalar type that can survive UE tuple copies.

    The validation payload is deliberately composed from plain Python values, but
    UE 5.8 can return an ``unreal.Name`` inside a copied reflected struct.  Keep
    receipt writing fail-closed for every other unexpected object type.
    """
    if isinstance(value, unreal.Name):
        return name_text(value)
    raise TypeError(f"Object of type {value.__class__.__name__} is not JSON serializable")


def vector_dict(value) -> dict:
    return {"x": float(value.x), "y": float(value.y), "z": float(value.z)}


def vector_near(value, expected, tolerance=0.02) -> bool:
    return all(math.isfinite(float(component)) and abs(float(component) - target) <= tolerance
               for component, target in zip((value.x, value.y, value.z), expected))


def rotation_near(value, expected, tolerance=0.02) -> bool:
    return all(math.isfinite(float(component)) and abs(float(component) - target) <= tolerance
               for component, target in zip((value.roll, value.pitch, value.yaw), expected))


def actor_transform_is_identity(actor) -> bool:
    return (vector_near(actor.get_actor_location(), (0.0, 0.0, 0.0))
            and rotation_near(actor.get_actor_rotation(), (0.0, 0.0, 0.0))
            and vector_near(actor.get_actor_scale3d(), (1.0, 1.0, 1.0)))


def actors_of(world, actor_class):
    return list(unreal.GameplayStatics.get_all_actors_of_class(world, actor_class))


def require_one(world, actor_class, label):
    rows = actors_of(world, actor_class)
    if len(rows) != 1:
        raise RuntimeError(f"Expected exactly one {label}, found {len(rows)}")
    return rows[0]


def png_dimensions(path: Path):
    data = path.read_bytes()[:24]
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        return None
    return [int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")]


def file_ready(path: Path) -> bool:
    return path.is_file() and path.stat().st_size >= 1024


def body_signature(body) -> dict:
    quality = body.quality_evidence
    cycle = body.cycle_evidence
    return {
        "body_id": name_text(body.body_id),
        "vehicle_model_id": name_text(body.vehicle_model_id),
        "order_id": name_text(body.order_id),
        "base_kit_id": name_text(body.base_kit_id),
        "reservation_id": name_text(body.reservation_id),
        "weld_line_id": name_text(body.weld_line_id),
        "panels": [
            {
                "panel_id": name_text(panel.panel_id),
                "panel_type_id": name_text(panel.panel_type_id),
                "stillage_id": name_text(panel.stillage_id),
            }
            for panel in body.panels
        ],
        "quality_state": enum_name(body.quality_state),
        "quality_evidence": {
            "recipe_complete": bool(quality.recipe_complete),
            "fixture_program_correct": bool(quality.fixture_program_correct),
            "spot_operations_complete": bool(quality.spot_operations_complete),
            "mig_operations_complete": bool(quality.mig_operations_complete),
            "robot_calibration_in_tolerance": bool(quality.robot_calibration_in_tolerance),
            "service_condition_acceptable": bool(quality.service_condition_acceptable),
            "safety_interlock_clear": bool(quality.safety_interlock_clear),
            "reason_codes": [name_text(code) for code in quality.reason_codes],
        },
        "cycle_evidence": {
            "closure_preparation_seconds": float(cycle.closure_preparation_seconds),
            "framing_seconds": float(cycle.framing_seconds),
            "welding_seconds": float(cycle.welding_seconds),
            "geometry_check_seconds": float(cycle.geometry_check_seconds),
            "completion_sequence": int(cycle.completion_sequence),
        },
        "ed_accepted": bool(body.ed_accepted),
    }


def wip_signature(wip) -> dict:
    return {
        "version": int(wip.version),
        "unit_id": name_text(wip.unit_id),
        "material_id": name_text(wip.material_id),
        "current_cell_id": name_text(wip.current_cell_id),
        "carrier_id": name_text(wip.carrier_id),
        "genealogy_sequence": int(wip.genealogy_sequence),
        "source_body_in_white": body_signature(wip.source_body_in_white),
    }


def record_screenshot(path: Path, source: str, hud_required: bool):
    if not file_ready(path):
        raise RuntimeError(f"Screenshot is absent or too small: {path}")
    payload["screenshots"][path.name] = {
        "path": str(path),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "dimensions": png_dimensions(path),
        "source": source,
        "hud_required": hud_required,
    }


def preflight():
    for path in (MAP_FILE, CREATE_RECEIPT, VALIDATION_RECEIPT, SCRIPT_FILE):
        if not path.is_file():
            raise RuntimeError(f"Missing required Paint evidence file: {path}")
    map_hash = sha256(MAP_FILE)
    create_hash = sha256(CREATE_RECEIPT)
    validation_hash = sha256(VALIDATION_RECEIPT)
    create = load_json(CREATE_RECEIPT)
    validation = load_json(VALIDATION_RECEIPT)
    if map_hash != EXPECTED_MAP_SHA256:
        raise RuntimeError(f"Paint map hash drift: {map_hash}")
    if create_hash != EXPECTED_CREATE_SHA256:
        raise RuntimeError(f"Paint creation receipt hash drift: {create_hash}")
    if validation_hash != EXPECTED_VALIDATION_SHA256:
        raise RuntimeError(f"Paint independent validation receipt hash drift: {validation_hash}")
    if (create.get("$schema") != "lineboss/audit/paint-shop/prototype-map-create-v001/v1"
            or create.get("status") != "PASS__ISOLATED_PAINT_SHOP_ONE_BOOTSTRAP_ZERO_MAP_OWNED_PRODUCTION"
            or create.get("builder_script_sha256") != EXPECTED_BUILDER_SHA256
            or create.get("map_sha256") != EXPECTED_MAP_SHA256):
        raise RuntimeError("Paint creation receipt contract drift")
    if (validation.get("$schema") != "lineboss/audit/paint-shop/prototype-map-validation-v001/v1"
            or validation.get("status") != "PASS__FRESH_RELOAD_PAINT_SHOP_PROTOTYPE_MAP_V001"
            or validation.get("failures")
            or validation.get("builder_script_sha256") != EXPECTED_BUILDER_SHA256
            or validation.get("validator_script_sha256") != EXPECTED_VALIDATOR_SHA256
            or validation.get("creation_receipt_sha256") != EXPECTED_CREATE_SHA256
            or validation.get("map_sha256") != EXPECTED_MAP_SHA256):
        raise RuntimeError("Paint independent validation receipt contract drift")
    return create_hash, validation_hash


CREATE_HASH, VALIDATION_HASH = preflight()
MAP_SHA_BEFORE = sha256(MAP_FILE)
RUN_DIR.mkdir(parents=True, exist_ok=True)
if AUDIT.exists():
    raise RuntimeError(f"Refusing to overwrite live Paint receipt: {AUDIT}")
if CAPTURE_DIR.exists():
    if not CAPTURE_DIR.is_dir() or any(CAPTURE_DIR.iterdir()):
        raise RuntimeError(f"Fresh Paint capture directory is not empty: {CAPTURE_DIR}")
else:
    CAPTURE_DIR.mkdir(parents=True, exist_ok=False)

payload = {
    "$schema": "lineboss/audit/paint-shop/actual-player-edcoat-pie-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "IN_PROGRESS",
    "failures": [],
    "map": MAP,
    "map_sha256_before": MAP_SHA_BEFORE,
    "map_sha256_after": None,
    "map_hash_unchanged": False,
    "validator_script": "Scripts/validate_paint_shop_actual_player_edcoat_pie_v001.py",
    "validator_script_sha256": sha256(SCRIPT_FILE),
    "prerequisites": {
        "creation_receipt": {
            "path": str(CREATE_RECEIPT),
            "sha256": CREATE_HASH,
        },
        "independent_map_validation": {
            "path": str(VALIDATION_RECEIPT),
            "sha256": VALIDATION_HASH,
        },
    },
    "saved_content_mutation_requested": False,
    "transient_camera_spawned": False,
    "validation_weld_source": {
        "editor_actor_unsaved": True,
        "editor_actor_transient_flag": False,
        "reason": "RF_Transient actors are deliberately excluded from PIE world duplication",
        "configured_only_in_game_world": True,
        "destroyed_after_end_play": False,
    },
    "checks": {},
    "screenshots": {},
}

LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
EDITOR_WORLDS = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
EDITOR_ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

started = time.monotonic()
phase_started = started
phase = "starting"
tick_handle = None
editor_weld_source = None
capture_task = None
capture_scene_path = None
capture_ui_expected = None
capture_ui_actual = None
capture_next_phase = None
final_status_requested = None
final_detail = ""
original_body = None
accepted_wip = None
output_ready_wip = None


def validate_player_and_cell(world):
    game_mode = require_one(world, unreal.LBPaintShopPrototypeGameMode, "Paint GameMode")
    bootstrap = require_one(world, unreal.LBPaintShopPrototypeWorldBootstrap, "Paint bootstrap")
    authority = require_one(world, unreal.LBPaintShopBuildAuthority, "Paint build authority")
    runtime = require_one(world, unreal.LBPaintShopPrototypeRuntime, "Paint runtime")
    cell = require_one(world, unreal.LBPaintShopCellActor, "Paint ED-coat cell")
    pawn = require_one(world, unreal.LBPaintShopManagementPawn, "Paint management pawn")
    hud = require_one(world, unreal.LBPaintShopPrototypeHUD, "Paint HUD")
    controller = unreal.GameplayStatics.get_player_controller(world, 0)
    if controller is None:
        raise RuntimeError("No player controller in actual Paint PIE")
    if (unreal.GameplayStatics.get_player_pawn(world, 0) != pawn
            or controller.get_controlled_pawn() != pawn or controller.get_view_target() != pawn
            or controller.get_hud() != hud):
        raise RuntimeError("Actual Paint controller is not possessing/viewing the exact management pawn and HUD")
    if (not game_mode.validate_prototype_shell_now(controller)
            or not game_mode.has_valid_prototype_bootstrap()
            or not game_mode.has_focused_management_camera()
            or game_mode.get_prototype_bootstrap() != bootstrap):
        raise RuntimeError("Paint player shell did not validate its exact bootstrap and camera")
    if (not bootstrap.is_ready() or bootstrap.has_failed()
            or enum_name(bootstrap.get_bootstrap_state()) != "READY"):
        raise RuntimeError("Paint bootstrap is not Ready")
    if (bootstrap.get_build_authority() != authority or bootstrap.get_runtime() != runtime
            or authority.get_owner() != bootstrap or runtime.get_owner() != bootstrap
            or cell.get_owner() != authority or runtime.get_build_authority() != authority
            or runtime.get_ed_coat_cell() != cell):
        raise RuntimeError("Paint bootstrap/authority/runtime/cell ownership is incoherent")
    if (not pawn.is_bound_to_prototype_bootstrap(bootstrap)
            or abs(float(pawn.get_prototype_zoom_distance()) - 2700.0) > 0.1
            or str(pawn.get_camera_status()) != "FOCUSED ON 1800 X 1000 CM ED-COAT CELL"):
        raise RuntimeError("Paint management pawn is not at the exact ED-coat focus contract")
    if (not cell.is_configured()
            or name_text(cell.get_cell_id()) != "PAINT_EDCOAT_CELL_001"
            or name_text(cell.get_definition_id()) != "PAINT_ED_COAT_DIP_CELL"
            or not actor_transform_is_identity(cell)):
        raise RuntimeError("Canonical Paint ED-coat cell identity or placement drift")

    placement = authority.validate_approved_cell_placement_for_validation(
        unreal.Name("PAINT_ED_COAT_DIP_CELL"), cell.get_actor_transform())
    if not isinstance(placement, tuple) or len(placement) != 2 or placement[0] is not True:
        raise RuntimeError(f"Approved ED-coat placement wrapper rejected canonical placement: {placement}")

    input_port = cell.get_input_port()
    output_port = cell.get_output_port()
    input_transform = None if input_port is None else input_port.get_configured_local_transform()
    output_transform = None if output_port is None else output_port.get_configured_local_transform()
    if (input_port is None or output_port is None
            or input_transform is None or output_transform is None
            or not input_port.is_configured() or not output_port.is_configured()
            or name_text(input_port.get_port_id()) != "CARRIER_IN"
            or name_text(input_port.get_wip_id()) != "BIW_COMPLETE"
            or name_text(output_port.get_port_id()) != "CARRIER_OUT"
            or name_text(output_port.get_wip_id()) != "BIW_ED_COATED"
            or not vector_near(input_transform.translation, (-900.0, 0.0, 430.0))
            or not vector_near(input_transform.rotation.rotator().get_forward_vector(),
                               (-1.0, 0.0, 0.0), 0.001)
            or not vector_near(output_transform.translation, (900.0, 0.0, 430.0))
            or not vector_near(output_transform.rotation.rotator().get_forward_vector(),
                               (1.0, 0.0, 0.0), 0.001)):
        raise RuntimeError("Paint carrier input/output port contract drift")

    footprint = cell.get_footprint()
    envelope = cell.get_protected_envelope()
    asset_paths = [str(path) for path in cell.get_required_presentation_asset_paths()]
    if (footprint is None or envelope is None
            or not vector_near(footprint.get_unscaled_box_extent(), (900.0, 500.0, 426.5))
            or not vector_near(envelope.get_unscaled_box_extent(), (950.0, 650.0, 475.0))
            or enum_name(footprint.get_collision_enabled()) != "QUERY_AND_PHYSICS"
            or enum_name(envelope.get_collision_enabled()) != "QUERY_ONLY"
            or not cell.has_complete_presentation_asset_set()
            or asset_paths != EXPECTED_ASSET_PATHS
            or not cell.are_candidate_meshes_visual_only()
            or int(cell.get_profiled_rail_segment_count()) != 48
            or not cell.is_profiled_rail_visual_only()):
        raise RuntimeError("Paint ED-coat physical/presentation asset contract drift")

    if (not runtime.is_initialized() or not runtime.is_starved() or runtime.has_active_wip()
            or runtime.is_paused() or runtime.is_output_blocked()
            or runtime.is_process_faulted() or enum_name(runtime.get_phase()) != "STARVED"
            or abs(float(runtime.get_cycle_progress01())) > 0.0001):
        raise RuntimeError("Fresh Paint runtime is not exactly starved and empty")

    weld_sources = [actor for actor in actors_of(world, unreal.LBBodyWeldLineActor)
                    if actor.actor_has_tag(SOURCE_TAG)]
    if len(weld_sources) != 1:
        raise RuntimeError(f"Expected exactly one duplicated validation Weld source, found {len(weld_sources)}")
    weld = weld_sources[0]
    weld_isolation_before = {
        "hidden_in_game": bool(weld.hidden),
        "collision_enabled": bool(weld.get_actor_enable_collision()),
        "actor_tick_enabled": bool(weld.is_actor_tick_enabled()),
    }
    # PIE reconstructs native actor ticking from the class tick defaults rather than
    # retaining the editor-instance tick registration state.  This actor is only an
    # unsaved validation data source, so enforce its isolation again in the game world
    # before any weld record is manufactured or acknowledged.
    weld.set_actor_hidden_in_game(True)
    weld.set_actor_enable_collision(False)
    weld.set_actor_tick_enabled(False)
    weld_isolation_after = {
        "hidden_in_game": bool(weld.hidden),
        "collision_enabled": bool(weld.get_actor_enable_collision()),
        "actor_tick_enabled": bool(weld.is_actor_tick_enabled()),
    }
    weld_isolation_passed = (
        weld_isolation_after["hidden_in_game"]
        and not weld_isolation_after["collision_enabled"]
        and not weld_isolation_after["actor_tick_enabled"]
        and vector_near(weld.get_actor_location(), (0.0, 0.0, -100000.0))
    )
    payload["checks"]["validation_weld_source_isolation"] = {
        "passed": weld_isolation_passed,
        "world_copy_before_enforcement": weld_isolation_before,
        "world_copy_after_enforcement": weld_isolation_after,
        "location_cm": vector_dict(weld.get_actor_location()),
        "source_tag": name_text(SOURCE_TAG),
    }
    if not weld_isolation_passed:
        raise RuntimeError("Validation Weld game-world source could not be held hidden/collision-off/tick-off")

    payload["checks"]["actual_player_shell"] = {
        "passed": True,
        "controller_possesses_management_pawn": True,
        "controller_view_target_is_management_pawn": True,
        "hud_is_paint_hud": True,
        "bootstrap_state": enum_name(bootstrap.get_bootstrap_state()),
        "camera_status": str(pawn.get_camera_status()),
        "zoom_distance_cm": float(pawn.get_prototype_zoom_distance()),
    }
    payload["checks"]["canonical_edcoat_cell"] = {
        "passed": True,
        "cell_id": name_text(cell.get_cell_id()),
        "definition_id": name_text(cell.get_definition_id()),
        "placement_grid_cm": float(authority.get_placement_grid_cm()),
        "asset_paths": asset_paths,
        "profiled_rail_segments": int(cell.get_profiled_rail_segment_count()),
        "candidate_meshes_visual_only": True,
        "profiled_rail_visual_only": True,
        "footprint_extent_cm": vector_dict(footprint.get_unscaled_box_extent()),
        "protected_envelope_extent_cm": vector_dict(envelope.get_unscaled_box_extent()),
    }
    payload["checks"]["initial_starvation"] = {
        "passed": True,
        "phase": enum_name(runtime.get_phase()),
        "active_wip": False,
        "cycle_progress01": float(runtime.get_cycle_progress01()),
    }
    return game_mode, bootstrap, authority, runtime, cell, pawn, hud, controller, weld


def manufacture_truthful_weld_output(weld):
    line_id = unreal.Name("WL-PAINT-PIE-000001")
    order_id = unreal.Name("ORDER-PAINT-PIE-000001")
    vehicle_id = unreal.LBBodyWeldLineActor.get_vehicle_model_id()
    kit_type_id = unreal.LBBodyWeldLineActor.get_base_kit_type_id()
    families = list(unreal.LBBodyWeldLineActor.get_required_panel_families())
    if len(families) != 11:
        raise RuntimeError(f"Expected 11 required Cairnwell panel families, found {len(families)}")
    if not weld.configure(line_id) or not weld.set_assigned_order(order_id):
        raise RuntimeError("Could not configure validation Weld source and assign its order")
    conditions = unreal.LBBodyWeldQualityConditions(
        fixture_program_correct=True,
        robot_calibration_in_tolerance=True,
        service_condition_acceptable=True,
        safety_interlock_clear=True,
    )
    weld.set_quality_conditions(conditions)
    for serial, family in enumerate(families, 1):
        family_text = name_text(family)
        stillage_id = unreal.Name(f"PAINT-PIE-STILLAGE-{family_text}-{serial:06d}")
        panel = unreal.LBBodyWeldPanelUnit(
            panel_id=unreal.Name(
                f"PTR-PANEL-{name_text(vehicle_id)}-{family_text}-{serial:06d}"),
            order_id=order_id,
            vehicle_model_id=vehicle_id,
            panel_type_id=family,
            stillage_id=stillage_id,
            reserved=False,
            consumed=False,
        )
        stillage = unreal.LBBodyWeldStillageInventory(
            stillage_id=stillage_id,
            order_id=order_id,
            vehicle_model_id=vehicle_id,
            panel_type_id=family,
            delivery_sequence=serial,
            capacity_panels=1,
            panel_units=[panel],
            empty_return_queued=False,
            empty_return_issued=False,
        )
        if weld.receive_panel_stillage(stillage) is None:
            raise RuntimeError(f"Weld rejected exact panel stillage {stillage_id}")
    base_kit = unreal.LBBodyWeldBaseKitUnit(
        kit_id=unreal.Name("PAINT-PIE-BASE-KIT-000001"),
        kit_type_id=kit_type_id,
        order_id=order_id,
        vehicle_model_id=vehicle_id,
        delivery_sequence=1,
        reserved=False,
        consumed=False,
    )
    if weld.receive_base_kit(base_kit) is None:
        raise RuntimeError("Weld rejected exact Paint PIE base kit")
    weld.set_ed_available(True)
    if weld.try_reserve_recipe() is None or weld.get_active_reservation() is None:
        raise RuntimeError("Weld could not reserve the exact complete-car recipe")
    if weld.commit_reserved_inputs() is None:
        raise RuntimeError("Weld could not commit its exact reserved inputs")
    weld.advance_simulation(22.0)
    body = weld.get_output_body()
    if body is None:
        raise RuntimeError("Weld did not produce a completed BIW after its exact 22-second recipe")
    signature = body_signature(body)
    quality = signature["quality_evidence"]
    if (signature["quality_state"] != "GOOD" or signature["ed_accepted"]
            or len(signature["panels"]) != 11 or len({row["panel_type_id"] for row in signature["panels"]}) != 11
            or not all(quality[key] for key in (
                "recipe_complete", "fixture_program_correct", "spot_operations_complete",
                "mig_operations_complete", "robot_calibration_in_tolerance",
                "service_condition_acceptable", "safety_interlock_clear"))
            or quality["reason_codes"]):
        raise RuntimeError("Completed Weld body lacks exact Good eleven-panel evidence")
    payload["checks"]["truthful_weld_output"] = {
        "passed": True,
        "line_id": name_text(line_id),
        "required_panel_family_count": len(families),
        "body": signature,
    }
    return body


def accept_weld_output(runtime, weld, body):
    global accepted_wip
    before = body_signature(body)
    result = runtime.accept_and_acknowledge_body_in_white(
        weld, body.body_id, unreal.Name("CARRIER-PAINT-PIE-001"))
    if result is None:
        raise RuntimeError("Paint rejected the exact completed Weld body")
    wip = runtime.get_active_wip()
    if wip is None:
        raise RuntimeError("Paint reported successful handoff without active WIP")
    accepted = wip_signature(wip)
    expected_body = dict(before)
    expected_body["ed_accepted"] = True
    if (weld.get_output_body() is not None or int(weld.get_completed_body_count()) != 1
            or not runtime.has_active_wip() or accepted["version"] != 2
            or accepted["unit_id"] != "PAINT_WIP_000001"
            or accepted["material_id"] != "BIW_COMPLETE"
            or accepted["current_cell_id"] != "PAINT_EDCOAT_CELL_001"
            or accepted["carrier_id"] != "CARRIER-PAINT-PIE-001"
            or accepted["source_body_in_white"] != expected_body):
        raise RuntimeError("Atomic Weld-to-Paint handoff failed exact identity or no-duplicate proof")
    runtime.advance_simulation(0.0)
    runtime.set_paused(True)
    if not runtime.is_paused():
        raise RuntimeError("Paint runtime did not pause immediately after accepted load presentation")
    accepted_wip = accepted
    payload["checks"]["exact_weld_to_paint_handoff"] = {
        "passed": True,
        "weld_output_consumed": True,
        "weld_completed_body_count": int(weld.get_completed_body_count()),
        "paint_wip": accepted,
    }


def start_capture_pair(world, scene_name, ui_name, next_phase):
    global phase, phase_started, capture_task, capture_scene_path
    global capture_ui_expected, capture_ui_actual, capture_next_phase
    scene_path = CAPTURE_DIR / scene_name
    ui_expected = CAPTURE_DIR / ui_name
    ui_actual = ui_expected.with_name(f"{ui_expected.stem}00000{ui_expected.suffix}")
    for path in (scene_path, ui_expected, ui_actual):
        if path.exists():
            raise RuntimeError(f"Refusing to overwrite Paint screenshot: {path}")
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    task = unreal.AutomationLibrary.take_high_res_screenshot(
        1920, 1080, str(scene_path), force_game_view=False)
    if not task.is_valid_task():
        raise RuntimeError(f"Invalid actual-player screenshot task: {scene_name}")
    capture_task = task
    capture_scene_path = scene_path
    capture_ui_expected = ui_expected
    capture_ui_actual = ui_actual
    capture_next_phase = next_phase
    phase = "wait_capture_scene"
    phase_started = time.monotonic()


def continue_capture_pair(world, now):
    global phase, phase_started, capture_task
    if phase == "wait_capture_scene":
        if now - phase_started < 2.0 or not capture_task.is_task_done():
            return False
        if not file_ready(capture_scene_path):
            return False
        dimensions = png_dimensions(capture_scene_path)
        if dimensions != [1920, 1080]:
            raise RuntimeError(f"High-resolution Paint screenshot is not 1920x1080: {dimensions}")
        record_screenshot(capture_scene_path, "possessed_paint_management_pawn", False)
        # The latent high-resolution task is complete at this point.  Release
        # the strong reference before waiting on the independent Slate shot so
        # a missing UI file can still take the normal EndPlay failure path.
        capture_task = None
        command = (f'SHOT SHOWUI filename="{str(capture_ui_expected).replace(chr(92), "/")}" '
                   "nosuffix")
        unreal.SystemLibrary.execute_console_command(world, command)
        phase = "wait_capture_ui"
        phase_started = now
        return False
    if phase == "wait_capture_ui":
        if now - phase_started < 1.0:
            return False
        source = capture_ui_expected if file_ready(capture_ui_expected) else capture_ui_actual
        if not file_ready(source):
            return False
        if source != capture_ui_expected:
            source.replace(capture_ui_expected)
        record_screenshot(capture_ui_expected, "possessed_paint_management_pawn_slate_ui", True)
        capture_task = None
        phase = capture_next_phase
        phase_started = now
        return True
    return False


def validate_carrier_rendered(world, cell, controller, stage_name):
    components = {
        "trolley": cell.get_carrier_trolley_presentation(),
        "hoist": cell.get_carrier_hoist_presentation(),
        "hanger": cell.get_carrier_hanger_presentation(),
        "proxy_biw": cell.get_proxy_biw_presentation(),
    }
    viewport = controller.get_viewport_size()
    rows = {}
    for label, component in components.items():
        if component is None:
            raise RuntimeError(f"Missing carrier presentation component {label}")
        origin, extent, radius = unreal.SystemLibrary.get_component_bounds(component)
        projected = unreal.GameplayStatics.project_world_to_screen(
            controller, origin, player_viewport_relative=True)
        on_screen = (projected is not None and 0.0 <= float(projected.x) <= float(viewport[0])
                     and 0.0 <= float(projected.y) <= float(viewport[1]))
        recent = bool(component.was_recently_rendered(3.0))
        visible = bool(component.is_visible())
        rows[label] = {
            "visible": visible,
            "recently_rendered": recent,
            "bounds_origin": vector_dict(origin),
            "bounds_extent": vector_dict(extent),
            "bounds_radius": float(radius),
            "projected": None if projected is None else [float(projected.x), float(projected.y)],
            "on_screen": on_screen,
        }
        if not visible or not recent:
            raise RuntimeError(f"Carrier presentation {label} was not visibly rendered during {stage_name}")
    if not rows["hanger"]["on_screen"] or not rows["proxy_biw"]["on_screen"]:
        raise RuntimeError(f"Paint body/hanger were outside the possessed-player view during {stage_name}")
    return {"passed": True, "viewport": [int(viewport[0]), int(viewport[1])], "components": rows}


def request_finish(status, detail=""):
    global phase, phase_started, final_status_requested, final_detail
    if phase in {"ending_pie", "finalizing"}:
        return
    if capture_task is not None:
        raise RuntimeError("Refusing to end PIE while an actual-player screenshot task is pending")
    final_status_requested = status
    final_detail = detail
    phase = "ending_pie"
    phase_started = time.monotonic()
    LEVELS.editor_request_end_play()


def fail(message):
    unreal.log_error("LINE_BOSS_PAINT_SHOP_ACTUAL_PLAYER_PIE_FAIL " + message)
    payload["failures"].append(message)
    try:
        request_finish("FAIL__PAINT_SHOP_ACTUAL_PLAYER_ED_COAT_PIE_V001", message)
    except Exception as nested:
        payload["failures"].append(f"Failure cleanup request also failed: {nested}")


def finalize_after_pie():
    global tick_handle, editor_weld_source, phase
    phase = "finalizing"
    cleanup_ok = False
    try:
        if editor_weld_source is not None:
            cleanup_ok = bool(EDITOR_ACTORS.destroy_actor(editor_weld_source))
            editor_weld_source = None
        if not cleanup_ok:
            payload["failures"].append("Unsaved editor-world validation Weld actor was not destroyed")
        payload["validation_weld_source"]["destroyed_after_end_play"] = cleanup_ok
    except Exception as exc:
        payload["failures"].append(f"Could not destroy unsaved editor-world Weld actor: {exc}")

    payload["map_sha256_after"] = sha256(MAP_FILE)
    payload["map_hash_unchanged"] = payload["map_sha256_after"] == MAP_SHA_BEFORE
    if not payload["map_hash_unchanged"]:
        payload["failures"].append("Saved Paint map hash changed during actual-player PIE")

    required_checks = (
        "actual_player_shell", "canonical_edcoat_cell", "initial_starvation",
        "truthful_weld_output", "exact_weld_to_paint_handoff",
        "immersing_and_pause_no_drift", "immersing_presentation_rendered",
        "rising_transition", "output_blocked_retention",
        "output_ready_presentation_rendered", "released_to_starvation",
    )
    missing_checks = [name for name in required_checks
                      if not payload["checks"].get(name, {}).get("passed")]
    if missing_checks:
        payload["failures"].append("Missing required Paint live checks: " + ", ".join(missing_checks))
    if set(payload["screenshots"]) != set(SCREENSHOT_NAMES):
        payload["failures"].append(
            "Actual-player screenshot inventory mismatch: "
            + ", ".join(sorted(payload["screenshots"])))
    for name, record in payload["screenshots"].items():
        path = Path(record["path"])
        if not file_ready(path) or sha256(path) != record["sha256"]:
            payload["failures"].append(f"Screenshot changed or disappeared before receipt finalization: {name}")

    payload["status"] = ("PASS__PAINT_SHOP_ACTUAL_PLAYER_ED_COAT_PIE_V001"
                         if final_status_requested == "PASS__PAINT_SHOP_ACTUAL_PLAYER_ED_COAT_PIE_V001"
                         and not payload["failures"]
                         else "FAIL__PAINT_SHOP_ACTUAL_PLAYER_ED_COAT_PIE_V001")
    payload["detail"] = final_detail
    payload["finished_utc"] = datetime.now(timezone.utc).isoformat()
    AUDIT.write_text(
        json.dumps(payload, indent=2, default=json_default) + "\n",
        encoding="utf-8",
    )
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)


def tick(_delta_seconds):
    global phase, phase_started, original_body, output_ready_wip
    now = time.monotonic()
    world = EDITOR_WORLDS.get_game_world()
    if phase == "ending_pie":
        if world is None:
            finalize_after_pie()
        elif now - phase_started > 20.0:
            payload["failures"].append("PIE did not end within 20 seconds")
            finalize_after_pie()
        return
    if phase == "finalizing":
        return
    if now - started > 150.0:
        fail("Timed out in Paint live PIE phase " + phase)
        return
    if world is None:
        return
    try:
        if phase in {"wait_capture_scene", "wait_capture_ui"}:
            continue_capture_pair(world, now)
            return

        if phase == "wait_world":
            if now - phase_started < 4.0:
                return
            (_game_mode, _bootstrap, _authority, runtime, cell, _pawn, _hud,
             controller, weld) = validate_player_and_cell(world)
            start_capture_pair(
                world,
                "01_actual_management_pawn_overview.png",
                "01_actual_management_pawn_overview_with_ui.png",
                "prepare_handoff")
            return

        runtime = require_one(world, unreal.LBPaintShopPrototypeRuntime, "Paint runtime")
        cell = require_one(world, unreal.LBPaintShopCellActor, "Paint ED-coat cell")
        controller = unreal.GameplayStatics.get_player_controller(world, 0)
        weld_sources = [actor for actor in actors_of(world, unreal.LBBodyWeldLineActor)
                        if actor.actor_has_tag(SOURCE_TAG)]
        if len(weld_sources) != 1:
            raise RuntimeError("Validation Weld source cardinality changed during PIE")
        weld = weld_sources[0]

        if phase == "prepare_handoff":
            original_body = manufacture_truthful_weld_output(weld)
            accept_weld_output(runtime, weld, original_body)
            runtime.set_paused(False)
            runtime.advance_simulation(4.0)
            runtime.set_paused(True)
            paused_cycle = float(runtime.get_cycle_progress01())
            paused_phase = float(runtime.get_phase_progress01())
            paused_wip = runtime.get_active_wip()
            if (enum_name(runtime.get_phase()) != "IMMERSING" or not runtime.is_paused()
                    or abs(paused_cycle - 0.4) > 0.0001 or paused_wip is None
                    or name_text(paused_wip.material_id) != "BIW_COMPLETE"):
                raise RuntimeError("Paint did not reach exact paused 0.4 Immersing state")
            paused_signature = wip_signature(paused_wip)
            runtime.advance_simulation(100.0)
            after_paused = runtime.get_active_wip()
            if (after_paused is None or abs(float(runtime.get_cycle_progress01()) - paused_cycle) > 0.0001
                    or abs(float(runtime.get_phase_progress01()) - paused_phase) > 0.0001
                    or wip_signature(after_paused) != paused_signature):
                raise RuntimeError("Paused ED-coat process drifted under a 100-second advance request")
            presentation = cell.capture_presentation_state()
            if (not presentation.carrier_visible
                    or abs(float(presentation.cycle_progress01) - 0.4) > 0.0001):
                raise RuntimeError("Immersing presentation did not show the exact carrier position")
            payload["checks"]["immersing_and_pause_no_drift"] = {
                "passed": True,
                "phase": enum_name(runtime.get_phase()),
                "cycle_progress01": paused_cycle,
                "phase_progress01": paused_phase,
                "material_id": name_text(after_paused.material_id),
                "paused_advance_request_seconds": 100.0,
                "carrier_visible": bool(presentation.carrier_visible),
            }
            start_capture_pair(
                world, "02_edcoat_immersing.png", "02_edcoat_immersing_with_ui.png",
                "verify_immersing_render")
            return

        if phase == "verify_immersing_render":
            payload["checks"]["immersing_presentation_rendered"] = validate_carrier_rendered(
                world, cell, controller, "Immersing")
            runtime.set_paused(False)
            runtime.advance_simulation(3.0)
            runtime.set_paused(True)
            if (enum_name(runtime.get_phase()) != "RISING"
                    or abs(float(runtime.get_cycle_progress01()) - 0.7) > 0.0001):
                raise RuntimeError("Paint did not make its exact Immersing-to-Rising transition")
            payload["checks"]["rising_transition"] = {
                "passed": True,
                "phase": enum_name(runtime.get_phase()),
                "cycle_progress01": float(runtime.get_cycle_progress01()),
            }
            runtime.set_output_blocked(True)
            runtime.set_paused(False)
            runtime.advance_simulation(3.0)
            ready = runtime.get_active_wip()
            if (enum_name(runtime.get_phase()) != "OUTPUT_READY"
                    or abs(float(runtime.get_cycle_progress01()) - 1.0) > 0.0001
                    or not runtime.is_output_blocked() or ready is None
                    or name_text(ready.material_id) != "BIW_ED_COATED"):
                raise RuntimeError("Paint did not retain exact ED-coated output in blocked OutputReady")
            output_ready_wip = wip_signature(ready)
            if runtime.release_output() is not None or not runtime.has_active_wip():
                raise RuntimeError("Blocked Paint output released or deleted the coated body")
            payload["checks"]["output_blocked_retention"] = {
                "passed": True,
                "phase": enum_name(runtime.get_phase()),
                "cycle_progress01": float(runtime.get_cycle_progress01()),
                "output_blocked": bool(runtime.is_output_blocked()),
                "retained_wip": output_ready_wip,
            }
            start_capture_pair(
                world, "03_edcoat_output_ready.png", "03_edcoat_output_ready_with_ui.png",
                "verify_output_render")
            return

        if phase == "verify_output_render":
            payload["checks"]["output_ready_presentation_rendered"] = validate_carrier_rendered(
                world, cell, controller, "OutputReady")
            runtime.set_output_blocked(False)
            released_result = runtime.release_output()
            if released_result is None or not isinstance(released_result, tuple) or len(released_result) != 2:
                raise RuntimeError("Unblocked Paint output did not return its exact coated WIP")
            released, reason = released_result
            released_signature = wip_signature(released)
            presentation = cell.capture_presentation_state()
            if (str(reason) != "" or released_signature != output_ready_wip
                    or runtime.has_active_wip() or not runtime.is_starved()
                    or enum_name(runtime.get_phase()) != "STARVED"
                    or presentation.carrier_visible):
                raise RuntimeError("Paint release did not preserve WIP lineage and return to empty starvation")
            payload["checks"]["released_to_starvation"] = {
                "passed": True,
                "released_wip": released_signature,
                "phase_after_release": enum_name(runtime.get_phase()),
                "carrier_visible_after_release": bool(presentation.carrier_visible),
            }
            request_finish("PASS__PAINT_SHOP_ACTUAL_PLAYER_ED_COAT_PIE_V001")
    except Exception as exc:
        fail(str(exc))


try:
    if not LEVELS.load_level(MAP):
        raise RuntimeError(f"Could not load isolated Paint map: {MAP}")
    editor_weld_source = EDITOR_ACTORS.spawn_actor_from_class(
        unreal.LBBodyWeldLineActor,
        unreal.Vector(0.0, 0.0, -100000.0),
        unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0),
        transient=False,
    )
    if editor_weld_source is None:
        raise RuntimeError("Could not create unsaved validation Weld source in editor world")
    editor_weld_source.set_editor_property("tags", [SOURCE_TAG])
    editor_weld_source.set_actor_hidden_in_game(True)
    editor_weld_source.set_actor_enable_collision(False)
    editor_weld_source.set_actor_tick_enabled(False)
    if not editor_weld_source.actor_has_tag(SOURCE_TAG):
        raise RuntimeError("Unsaved validation Weld source did not retain its unique tag")
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    phase = "wait_world"
    phase_started = time.monotonic()
    tick_handle = unreal.register_slate_post_tick_callback(tick)
    LEVELS.editor_request_begin_play()
except Exception:
    if tick_handle is not None:
        try:
            unreal.unregister_slate_post_tick_callback(tick_handle)
        except Exception:
            pass
        tick_handle = None
    try:
        unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    except Exception:
        pass
    if editor_weld_source is not None:
        try:
            EDITOR_ACTORS.destroy_actor(editor_weld_source)
        except Exception:
            pass
    raise
