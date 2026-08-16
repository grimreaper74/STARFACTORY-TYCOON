"""Fail-closed live PIE gate for the Body Shop underbody release candidate.

This script deliberately uses the saved map's lighting, grid visibility, GameMode,
management pawn and HUD.  It never saves Content, spawns a review camera, or changes
the saved environment.  The only runtime mutation is inside PIE and the isolated
Body Shop experimental save slot.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)

ROOT = Path(unreal.Paths.project_dir()).resolve()
sys.path.insert(0, str(ROOT / "Scripts"))
from body_shop_support_kit_native_v002_contract import (  # noqa: E402
    validate as validate_support_kit,
)
MAP = "/Game/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001"
MAP_FILE = ROOT / "Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap"
RESTORED_PRESS_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001.umap"
EXPECTED_RESTORED_PRESS_SHA256 = "D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5"
MANAGEMENT_V005_VALIDATION = ROOT / "Saved/Audits/BodyShop/Experimental_v001/management_cutaway_v005_validation.json"
EXPECTED_VISUAL_V004_VALIDATION_SHA256 = "956E08511F2AA840D71B94E07217DBA357EA955B701BA3A8C9F744AAAC11757E"
EXPECTED_MANAGEMENT_V005_PATCH_SHA256 = "8A305B26C838567FC3F26063B28F9D7FA65382F9A932F762A8CC3C4DD7F7ED50"
EXPECTED_MANAGEMENT_V005_VALIDATION_SHA256 = "DCDBCBFA4D47FEBF21A22FD98F30ADC880D037519EBDBC6AE34BD7D4CE9F88D8"
EXPECTED_MANAGEMENT_V005_MAP_SHA256 = "8CB6976C532F5C06635ADC8ED00BB50CAF39FFCE2F15826C3456C6EDF4CACE8F"
FINAL_NATIVE_ROBOT_RUN = ROOT / "Saved/Audits/BodyShop/RobotNative_v001/UnrealImportLane/20260814T204134Z-19e41ca7"
FINAL_NATIVE_ROBOT_LANE_SUMMARY = FINAL_NATIVE_ROBOT_RUN / "lane_summary_v001.json"
FINAL_NATIVE_ROBOT_IMPORT_RECEIPT = FINAL_NATIVE_ROBOT_RUN / "import_receipt_v001.json"
FINAL_NATIVE_ROBOT_VALIDATION_RECEIPT = FINAL_NATIVE_ROBOT_RUN / "fresh_load_validation_receipt_v001.json"
FINAL_NATIVE_ROBOT_LANE_SUMMARY_SHA256 = "B1AFEDB019C28B04082497F46B954C29262D0A30B19854D00CF1168537AA2F73"
FINAL_NATIVE_ROBOT_IMPORT_RECEIPT_SHA256 = "B7738C068F344BBA391442F404E38A87BAF0C70B72A19CD2CA5DDDC68A5210BF"
FINAL_NATIVE_ROBOT_VALIDATION_RECEIPT_SHA256 = "9A4097CBB68F46297031A092FF861B20FC4B2F60576150005B483D984E26EBEA"
FINAL_NATIVE_ROBOT_BASELINE_SHA256 = "D967E8CD1596FC620066668138FEE14A47C702D55989FB1DB1C3AAF0ABF0FF31"
FINAL_NATIVE_ROBOT_CLEAN_DISPOSITION_SHA256 = "E9862B44C656586879EF3607C33BD8A536E9CE0D816C144AFF870C31A7B52BC3"
FINAL_NATIVE_ROBOT_TRIANGLE_TOTALS = [2628, 1964, 1356]
STAMP = os.environ.get("LB_BODYSHOP_VALIDATION_STAMP") or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
RUN_DIR = ROOT / "Saved/Audits/BodyShop/Experimental_v001/ReleaseValidation" / STAMP
CAPTURE_DIR = ROOT / "Saved/ValidationScreenshots/BodyShop/Experimental_v001/ReleaseValidation" / STAMP
AUDIT = RUN_DIR / "live_pie_release_validation_v003.json"
PERF_LOG = RUN_DIR / "performance_console_capture.log"
EXPECTED_DEFINITIONS = {
    "BW001_FULL_STILLAGE_DOCK_BASIC",
    "BW002_PANEL_PRESENTATION_BASIC",
    "BW003_UNDERBODY_FIXTURE_BASIC",
    "BW003_STRAIGHT_SKID_CONVEYOR_BASIC",
    "BW012_VISION_GATE_BASIC",
    "BW014_OUTPUT_BUFFER_BASIC",
}
EXPECTED_SLOTS = {"ROBOT_HND_01", "ROBOT_WELD_LEFT", "ROBOT_WELD_RIGHT"}
EXPECTED_SPOT_SLOTS = {"ROBOT_WELD_LEFT", "ROBOT_WELD_RIGHT"}
EXPECTED_NATIVE_ROBOT_COMPONENT_MESHES = {
    "BasePresentation": (
        "/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/"
        "SM_LB_BodyShopRobotNative_Base_v001.SM_LB_BodyShopRobotNative_Base_v001"
    ),
    **{
        f"J{joint}Presentation": (
            "/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/"
            f"SM_LB_BodyShopRobotNative_J{joint}_v001."
            f"SM_LB_BodyShopRobotNative_J{joint}_v001"
        )
        for joint in range(1, 7)
    },
}
EXPECTED_PANEL_PICK_TOOL = (
    "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Tools/"
    "SM_LB_BodyShopTool_PanelPick8Cup_v001.SM_LB_BodyShopTool_PanelPick8Cup_v001"
)
EXPECTED_NATIVE_OPEN_CGUN = (
    "/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Tools/"
    "SM_LB_BodyShopToolNative_OpenCGun_v001.SM_LB_BodyShopToolNative_OpenCGun_v001"
)
EXPECTED_PILOT_STILLAGE_MESH = (
    "/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Logistics/"
    "SM_LB_BodyShopSupport_PanelStillage_Full_v002."
    "SM_LB_BodyShopSupport_PanelStillage_Full_v002"
)
EXPECTED_SERVICE_ACTOR_NAME = "LB_BodyShop_ServiceDressing_v002"
EXPECTED_SERVICE_TAGS = {
    "LB.BodyShop.ServiceDressing.v002",
    "LB.Asset.CleanRoomNative.v002",
    "LB.NotProcessWIP",
}
EXPECTED_SERVICE_HISM = {
    "EmptyReturnCartNativeV002Instances": (
        "/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Logistics/"
        "SM_LB_BodyShopSupport_EmptyReturnCart_v002."
        "SM_LB_BodyShopSupport_EmptyReturnCart_v002",
        6,
    ),
    "ComponentServicePalletNativeV002Instances": (
        "/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Logistics/"
        "SM_LB_BodyShopSupport_ComponentServicePallet_v002."
        "SM_LB_BodyShopSupport_ComponentServicePallet_v002",
        3,
    ),
    "EmptySmallPartsCrateNativeV002Instances": (
        "/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Logistics/"
        "SM_LB_BodyShopSupport_SmallPartsCrate_Open_v002."
        "SM_LB_BodyShopSupport_SmallPartsCrate_Open_v002",
        3,
    ),
}
EXPECTED_CONVEYOR_CHAIN = (
    ("BW003_UNDERBODY_FIXTURE_BASIC", -4500.0, 1200.0),
    ("BW003_STRAIGHT_SKID_CONVEYOR_BASIC", -3400.0, 1000.0),
    ("BW012_VISION_GATE_BASIC", -2500.0, 800.0),
    ("BW014_OUTPUT_BUFFER_BASIC", -1600.0, 1000.0),
)
EXPECTED_PILOT_SKID_MESH = (
    "/Game/LineBoss/Candidates/Vehicles/Cairnwell2040/BIWBaseKitRuntime_v001/Carrier/"
    "SM_LB_C2040_BIWBaseSkid_v001.SM_LB_C2040_BIWBaseSkid_v001"
)
EXPECTED_PILOT_UNDERBODY_MESH = (
    "/Game/LineBoss/Candidates/Vehicles/Cairnwell2040/BIWBaseKitRuntime_v001/Workpiece/"
    "SM_LB_C2040_BIWBaseKit_Underbody_v001.SM_LB_C2040_BIWBaseKit_Underbody_v001"
)
PRESENTATION_TOLERANCE_CM = 0.1
MAP_SHA_BEFORE = hashlib.sha256(MAP_FILE.read_bytes()).hexdigest().upper()
RESTORED_PRESS_SHA_BEFORE = hashlib.sha256(
    RESTORED_PRESS_FILE.read_bytes()
).hexdigest().upper()
if RESTORED_PRESS_SHA_BEFORE != EXPECTED_RESTORED_PRESS_SHA256:
    raise RuntimeError("Live PIE capture requires the exact full restored Press map")
if not MANAGEMENT_V005_VALIDATION.is_file():
    raise RuntimeError(f"Missing management-cutaway v005 validation receipt: {MANAGEMENT_V005_VALIDATION}")
MANAGEMENT_V005_VALIDATION_SHA256 = hashlib.sha256(
    MANAGEMENT_V005_VALIDATION.read_bytes()).hexdigest().upper()
MANAGEMENT_V005_GATE = json.loads(MANAGEMENT_V005_VALIDATION.read_text(encoding="utf-8-sig"))
MANAGEMENT_V005_PREREQUISITES = MANAGEMENT_V005_GATE.get("prerequisites", {})
if (MANAGEMENT_V005_VALIDATION_SHA256 != EXPECTED_MANAGEMENT_V005_VALIDATION_SHA256
        or MANAGEMENT_V005_GATE.get("$schema")
            != "lineboss/audit/bodyshop/management-cutaway-v005-validation/v1"
        or MANAGEMENT_V005_GATE.get("status")
            != "PASS__FRESH_RELOAD_BODYSHOP_MANAGEMENT_CUTAWAY_V005"
        or MANAGEMENT_V005_GATE.get("failures")
        or MANAGEMENT_V005_PREREQUISITES.get(
            "visual_readability_v004_validation", {}).get("sha256")
            != EXPECTED_VISUAL_V004_VALIDATION_SHA256
        or MANAGEMENT_V005_PREREQUISITES.get(
            "management_cutaway_v005_patch", {}).get("sha256")
            != EXPECTED_MANAGEMENT_V005_PATCH_SHA256
        or MANAGEMENT_V005_GATE.get("map", {}).get("sha256")
            != EXPECTED_MANAGEMENT_V005_MAP_SHA256
        or MANAGEMENT_V005_GATE.get("map", {}).get(
            "read_only_fresh_load_hash_unchanged") is not True
        or MAP_SHA_BEFORE != EXPECTED_MANAGEMENT_V005_MAP_SHA256):
    raise RuntimeError("Live PIE capture requires the exact fresh management-cutaway v005 map authority")

for evidence, expected_hash in (
    (FINAL_NATIVE_ROBOT_LANE_SUMMARY, FINAL_NATIVE_ROBOT_LANE_SUMMARY_SHA256),
    (FINAL_NATIVE_ROBOT_IMPORT_RECEIPT, FINAL_NATIVE_ROBOT_IMPORT_RECEIPT_SHA256),
    (FINAL_NATIVE_ROBOT_VALIDATION_RECEIPT,
     FINAL_NATIVE_ROBOT_VALIDATION_RECEIPT_SHA256),
):
    if (not evidence.is_file()
            or hashlib.sha256(evidence.read_bytes()).hexdigest().upper() != expected_hash):
        raise RuntimeError("Live PIE capture requires exact final native robot evidence: " + str(evidence))
FINAL_NATIVE_ROBOT_GATE = json.loads(
    FINAL_NATIVE_ROBOT_VALIDATION_RECEIPT.read_text(encoding="utf-8-sig")
)
if (FINAL_NATIVE_ROBOT_GATE.get("status")
        != "PASS__INDEPENDENT_FRESH_PROCESS_LOAD__INCIDENT_ARCHIVE_VERIFIED__8_ASSETS_3_LODS_MONOTONIC_ONE_UV_BODYSHOP_ROBOT_NATIVE_V001"
        or FINAL_NATIVE_ROBOT_GATE.get("baseline_sha256")
            != FINAL_NATIVE_ROBOT_BASELINE_SHA256
        or FINAL_NATIVE_ROBOT_GATE.get("clean_disposition_contract_sha256")
            != FINAL_NATIVE_ROBOT_CLEAN_DISPOSITION_SHA256
        or FINAL_NATIVE_ROBOT_GATE.get("import_receipt_sha256")
            != FINAL_NATIVE_ROBOT_IMPORT_RECEIPT_SHA256
        or FINAL_NATIVE_ROBOT_GATE.get("asset_count") != 8
        or FINAL_NATIVE_ROBOT_GATE.get("lod_count_per_asset") != 3
        or FINAL_NATIVE_ROBOT_GATE.get("source_fbx_count") != 24
        or FINAL_NATIVE_ROBOT_GATE.get("strict_per_asset_triangle_monotonicity") is not True
        or FINAL_NATIVE_ROBOT_GATE.get("exactly_one_uv_channel_on_all_24_lods") is not True
        or FINAL_NATIVE_ROBOT_GATE.get("manual_lod_screen_sizes_persisted_after_fresh_process_load") is not True
        or FINAL_NATIVE_ROBOT_GATE.get("failures")):
    raise RuntimeError("Live PIE capture final native robot receipt contract drift")
FINAL_NATIVE_ROBOT_TRIANGLES = [
    sum(row["lods"][lod_index]["triangles"]
        for row in FINAL_NATIVE_ROBOT_GATE.get("assets", {}).values())
    for lod_index in range(3)
]
if FINAL_NATIVE_ROBOT_TRIANGLES != FINAL_NATIVE_ROBOT_TRIANGLE_TOTALS:
    raise RuntimeError("Live PIE capture final native robot triangle totals drift")
FINAL_NATIVE_SUPPORT_KIT = validate_support_kit(ROOT)
LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

RUN_DIR.mkdir(parents=True, exist_ok=True)
CAPTURE_DIR.mkdir(parents=True, exist_ok=False)

payload = {
    "$schema": "cairnwell/body-shop/experimental-v001/live-pie-release-validation/v3",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "IN_PROGRESS",
    "map": MAP,
    "map_sha256_before": MAP_SHA_BEFORE,
    "full_restored_press_sha256_before": RESTORED_PRESS_SHA_BEFORE,
    "prerequisites": {
        "management_cutaway_v005_validation": {
            "path": str(MANAGEMENT_V005_VALIDATION),
            "sha256": MANAGEMENT_V005_VALIDATION_SHA256,
            "schema": MANAGEMENT_V005_GATE.get("$schema"),
            "status": MANAGEMENT_V005_GATE.get("status"),
            "map_sha256": MANAGEMENT_V005_GATE.get("map", {}).get("sha256"),
        },
        "final_native_robot": {
            "lane_summary": str(FINAL_NATIVE_ROBOT_LANE_SUMMARY),
            "lane_summary_sha256": FINAL_NATIVE_ROBOT_LANE_SUMMARY_SHA256,
            "import_receipt": str(FINAL_NATIVE_ROBOT_IMPORT_RECEIPT),
            "import_receipt_sha256": FINAL_NATIVE_ROBOT_IMPORT_RECEIPT_SHA256,
            "validation_receipt": str(FINAL_NATIVE_ROBOT_VALIDATION_RECEIPT),
            "validation_receipt_sha256": FINAL_NATIVE_ROBOT_VALIDATION_RECEIPT_SHA256,
            "lod_triangle_totals": FINAL_NATIVE_ROBOT_TRIANGLES,
        },
        "final_native_support_kit_v002": FINAL_NATIVE_SUPPORT_KIT,
    },
    "saved_environment_defaults_only": True,
    "transient_camera_spawned": False,
    "transient_light_grid_or_postprocess_mutation": False,
    "actual_management_pawn_and_hud_required": True,
    "checks": {},
    "stage_joint_samples": [],
    "screenshots": [],
    "failures": [],
    "known_evidence_limits": [
        "Performance stat commands are requested and the run log is retained; a dedicated timed benchmark is still required for numeric release budgets.",
        "Cross-process save/restart/load is covered by packaged smoke log checks only if a packaged runtime automation bridge exists; otherwise packaging fails closed and records the gap.",
    ],
}

started = time.monotonic()
phase_started = started
phase = "wait_world"
tick_handle = None
capture_task = None
sampled_stages = set()
home_angles = {}
last_joint_sample = 0.0
ui_capture_path = None
welding_capture_world_time_marker = None
welding_pre_camera_skid_render_time = None
welding_pre_camera_underbody_render_time = None


def enum_text(value):
    text = str(value).upper()
    if "." in text:
        text = text.rsplit(".", 1)[-1]
    return text.split(":", 1)[0].strip("<> ")


def call_bool_with_reason(method):
    try:
        result = method()
    except TypeError:
        result = method("")
    if isinstance(result, tuple):
        return bool(result[0]), str(result[1]) if len(result) > 1 else ""
    if isinstance(result, bool):
        return result, ""
    # UE Python represents native bool + FString& functions as str on success
    # (the output reason, commonly empty) and None on failure.
    return result is not None, str(result or "")


def start_cycle(runtime):
    before = int(runtime.get_active_pilot_wip_count())
    try:
        result = runtime.start_pilot_cycle()
    except TypeError:
        result = runtime.start_pilot_cycle("")
    success = bool(runtime.is_simulation_running()) and int(runtime.get_active_pilot_wip_count()) == 1
    return success, {"python_return": repr(result), "wip_before": before,
                     "wip_after": int(runtime.get_active_pilot_wip_count()),
                     "stage_after": enum_text(runtime.get_runtime_stage())}


def actors_of(world, cls):
    return list(unreal.GameplayStatics.get_all_actors_of_class(world, cls))


def underbody_release_presentation_contract(cells):
    """Prove the exact derived presentation requested for the v005 player view."""
    by_definition = {str(cell.get_definition_id()): cell for cell in cells}
    if set(by_definition) != EXPECTED_DEFINITIONS:
        raise RuntimeError("Cannot validate presentation against an unexpected cell definition set")

    chain = []
    for definition_id, expected_x, expected_span in EXPECTED_CONVEYOR_CHAIN:
        cell = by_definition[definition_id]
        location = cell.get_actor_location()
        span = float(cell.get_skid_conveyor_presentation_span_cm())
        row = {
            "definition_id": definition_id,
            "world_location_cm": [round(float(location.x), 3), round(float(location.y), 3),
                                  round(float(location.z), 3)],
            "presentation_span_cm": round(span, 3),
            "world_min_x_cm": round(float(location.x) - span * 0.5, 3),
            "world_max_x_cm": round(float(location.x) + span * 0.5, 3),
            "has_automotive_skid_conveyor": bool(
                cell.has_automotive_skid_conveyor_presentation()),
            "structure_instances": int(cell.get_skid_conveyor_structure_instance_count()),
            "roller_instances": int(cell.get_skid_conveyor_roller_instance_count()),
            "safety_instances": int(cell.get_skid_conveyor_safety_instance_count()),
        }
        row["passed"] = (
            row["has_automotive_skid_conveyor"]
            and math.isclose(float(location.x), expected_x, rel_tol=0.0,
                             abs_tol=PRESENTATION_TOLERANCE_CM)
            and math.isclose(span, expected_span, rel_tol=0.0,
                             abs_tol=PRESENTATION_TOLERANCE_CM)
        )
        chain.append(row)

    joints = []
    for upstream, downstream in zip(chain, chain[1:]):
        gap = downstream["world_min_x_cm"] - upstream["world_max_x_cm"]
        joints.append({
            "upstream": upstream["definition_id"],
            "downstream": downstream["definition_id"],
            "gap_cm": round(gap, 3),
            "passed": abs(gap) <= PRESENTATION_TOLERANCE_CM,
        })

    underbody = by_definition["BW003_UNDERBODY_FIXTURE_BASIC"]
    underbody_row = next(row for row in chain
                         if row["definition_id"] == "BW003_UNDERBODY_FIXTURE_BASIC")
    main_path = str(underbody.get_main_presentation_asset_path())
    underbody_details = {
        "definition_id": "BW003_UNDERBODY_FIXTURE_BASIC",
        "main_presentation_asset_path": main_path,
        "no_underbody_main_presentation_mesh": main_path.strip() == "",
        "continuous_conveyor": underbody_row["has_automotive_skid_conveyor"],
        "conveyor_span_cm": underbody_row["presentation_span_cm"],
        "conveyor_structure_instances": underbody_row["structure_instances"],
        "conveyor_roller_instances": underbody_row["roller_instances"],
        "conveyor_safety_instances": underbody_row["safety_instances"],
        "painted_work_zone": bool(underbody.has_painted_underbody_work_zone()),
        "floor_working_zone_instances": int(
            underbody.get_cell_floor_working_zone_instance_count()),
        "floor_safety_marking_instances": int(
            underbody.get_cell_floor_safety_marking_instance_count()),
        "neutral_conveyor_lane_width_cm": float(
            underbody.get_cell_floor_neutral_conveyor_lane_width_cm()),
        "uses_open_rail_safety_presentation": bool(
            underbody.uses_open_rail_safety_presentation()),
        "auto_assembled_fence_segments": int(
            underbody.get_auto_assembled_fence_segment_count()),
    }
    underbody_passed = (
        underbody_details["no_underbody_main_presentation_mesh"]
        and underbody_details["continuous_conveyor"]
        and math.isclose(underbody_details["conveyor_span_cm"], 1200.0, rel_tol=0.0,
                         abs_tol=PRESENTATION_TOLERANCE_CM)
        and underbody_details["conveyor_structure_instances"] == 23
        and underbody_details["conveyor_roller_instances"] == 50
        and underbody_details["conveyor_safety_instances"] == 2
        and underbody_details["painted_work_zone"]
        and underbody_details["floor_working_zone_instances"] == 2
        and underbody_details["floor_safety_marking_instances"] == 6
        and math.isclose(underbody_details["neutral_conveyor_lane_width_cm"], 260.0,
                         rel_tol=0.0, abs_tol=PRESENTATION_TOLERANCE_CM)
        and underbody_details["uses_open_rail_safety_presentation"]
        and underbody_details["auto_assembled_fence_segments"] == 18
    )
    chain_passed = all(row["passed"] for row in chain) and all(
        joint["passed"] for joint in joints)
    receipt = {
        "passed": underbody_passed and chain_passed,
        "underbody_fixture": underbody_details,
        "continuous_conveyor_chain": {
            "passed": chain_passed,
            "tolerance_cm": PRESENTATION_TOLERANCE_CM,
            "cells": chain,
            "joints": joints,
        },
    }
    if not receipt["passed"]:
        raise RuntimeError("Underbody release presentation contract failed: " + repr(receipt))
    payload["checks"]["underbody_release_presentation_contract"] = receipt


def service_dressing_contract(world, runtime):
    services = actors_of(world, unreal.LBBodyShopServiceDressingActor)
    if len(services) != 1:
        raise RuntimeError(
            "Actual-player PIE requires exactly one service dressing actor, found "
            + str(len(services)))
    service = services[0]
    tags = {str(tag) for tag in service.tags}
    component_rows = []
    for component in service.get_components_by_class(
            unreal.HierarchicalInstancedStaticMeshComponent):
        name = component.get_name()
        if name not in EXPECTED_SERVICE_HISM:
            continue
        expected_mesh, expected_count = EXPECTED_SERVICE_HISM[name]
        mesh = component.get_editor_property("static_mesh")
        mesh_path = mesh.get_path_name() if mesh is not None else None
        count = int(component.get_instance_count())
        if mesh_path != expected_mesh or count != expected_count:
            raise RuntimeError(
                f"Actual-player service HISM drift: {name} mesh={mesh_path} count={count}")
        component_rows.append({
            "component": name,
            "mesh": mesh_path,
            "instance_count": count,
        })
    stillage_path = str(runtime.get_pilot_stillage_presentation_mesh_path())
    receipt = {
        "passed": (
            service.get_name() == EXPECTED_SERVICE_ACTOR_NAME
            and service.get_class().get_name() == "LBBodyShopServiceDressingActor"
            and EXPECTED_SERVICE_TAGS.issubset(tags)
            and bool(service.is_presentation_active())
            and bool(service.has_valid_presentation_contract())
            and not bool(service.represents_process_wip())
            and int(service.get_visible_instance_count()) == 12
            and {row["component"] for row in component_rows}
                == set(EXPECTED_SERVICE_HISM)
            and sum(row["instance_count"] for row in component_rows) == 12
            and stillage_path == EXPECTED_PILOT_STILLAGE_MESH
        ),
        "actor_count": len(services),
        "actor_name": service.get_name(),
        "actor_class": service.get_class().get_name(),
        "tags": sorted(tags),
        "presentation_active": bool(service.is_presentation_active()),
        "valid_presentation_contract": bool(service.has_valid_presentation_contract()),
        "represents_process_wip": bool(service.represents_process_wip()),
        "visible_instance_count": int(service.get_visible_instance_count()),
        "hism_batch_count": len(component_rows),
        "hism_instance_count": sum(
            row["instance_count"] for row in component_rows),
        "hism_components": sorted(
            component_rows, key=lambda row: row["component"]),
        "runtime_full_stillage_getter": (
            "ALBBodyShopPrototypeRuntime::GetPilotStillagePresentationMeshPath"
        ),
        "runtime_full_stillage_mesh_path": stillage_path,
        "all_service_dressing_is_non_wip": True,
    }
    if not receipt["passed"]:
        raise RuntimeError("Actual-player native support presentation drift: " + repr(receipt))
    payload["checks"]["native_support_service_dressing_v002"] = receipt


def actor_contract(world):
    bootstrap = actors_of(world, unreal.LBBodyShopPrototypeWorldBootstrap)
    runtime = actors_of(world, unreal.LBBodyShopPrototypeRuntime)
    authority = actors_of(world, unreal.LBBodyShopBuildAuthority)
    cells = actors_of(world, unreal.LBBodyShopCellActor)
    robots = actors_of(world, unreal.LBBodyShopRobotActor)
    pawns = actors_of(world, unreal.LBBodyShopManagementPawn)
    huds = actors_of(world, unreal.LBBodyShopPrototypeHUD)
    counts = {"bootstrap": len(bootstrap), "runtime": len(runtime), "authority": len(authority),
              "cells": len(cells), "robots": len(robots), "management_pawn": len(pawns), "hud": len(huds)}
    if counts != {"bootstrap": 1, "runtime": 1, "authority": 1, "cells": 6,
                  "robots": 3, "management_pawn": 1, "hud": 1}:
        raise RuntimeError(f"Unexpected actual-player/runtime actor counts: {counts}")
    player_pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
    player_controller = unreal.GameplayStatics.get_player_controller(world, 0)
    player_hud = player_controller.get_hud() if player_controller is not None else None
    if player_pawn != pawns[0] or player_hud != huds[0]:
        raise RuntimeError("The Body Shop management pawn/HUD exist but are not player possessed/active")
    root_widget = huds[0].get_prototype_root_widget()
    payload["checks"]["umg_runtime_diagnostics"] = {
        "widget_exists": root_widget is not None,
        "widget_in_viewport": bool(root_widget.is_in_viewport()) if root_widget is not None else False,
        "widget_visibility": enum_text(root_widget.get_visibility()) if root_widget is not None else "NONE",
        "renderable_shell": bool(root_widget.has_renderable_shell()) if root_widget is not None else False,
        "hud_tick_enabled": bool(huds[0].is_actor_tick_enabled()),
        "controller_is_local": bool(player_controller.is_local_controller()),
    }
    if not bool(huds[0].is_prototype_widget_active()):
        raise RuntimeError("The Body Shop HUD exists but its UMG-only operator shell is not active")
    definitions = {str(cell.get_definition_id()) for cell in cells}
    if definitions != EXPECTED_DEFINITIONS or not all(bool(cell.is_commissioned()) for cell in cells):
        raise RuntimeError(f"Six-cell definitions/commissioning invalid: {sorted(definitions)}")
    underbody_release_presentation_contract(cells)
    service_dressing_contract(world, runtime[0])
    rows = []
    for robot in robots:
        presentation_meshes = {}
        for component in robot.get_components_by_class(unreal.StaticMeshComponent):
            component_name = component.get_name()
            if component_name not in {
                *EXPECTED_NATIVE_ROBOT_COMPONENT_MESHES,
                "ToolPresentation",
            }:
                continue
            mesh = component.static_mesh
            if mesh is not None:
                presentation_meshes[component_name] = mesh.get_path_name()
        expected_tool = (
            EXPECTED_PANEL_PICK_TOOL
            if str(robot.get_slot_id()) == "ROBOT_HND_01"
            else EXPECTED_NATIVE_OPEN_CGUN
        )
        expected_presentation = {
            **EXPECTED_NATIVE_ROBOT_COMPONENT_MESHES,
            "ToolPresentation": expected_tool,
        }
        if presentation_meshes != expected_presentation:
            raise RuntimeError(
                f"Native Base/J1..J6/EOAT presentation drift for "
                f"{robot.get_slot_id()}: {presentation_meshes}"
            )
        rows.append({
            "slot": str(robot.get_slot_id()),
            "owning_cell": str(robot.get_owning_cell_id()),
            "configured": bool(robot.is_configured_for_authored_slot()),
            "complete_art": bool(robot.has_complete_art_presentation()),
            "cups": int(robot.get_vacuum_contact_socket_count()),
            "pose": enum_text(robot.get_current_pose()),
            "presentation_meshes": presentation_meshes,
            "tool_mesh": presentation_meshes["ToolPresentation"],
        })
    if {row["slot"] for row in rows} != EXPECTED_SLOTS:
        raise RuntimeError(f"Robot slot set is wrong: {rows}")
    if not all(row["configured"] and row["complete_art"] for row in rows):
        raise RuntimeError("A robot is not configured or lacks complete art")
    handler = next(row for row in rows if row["slot"] == "ROBOT_HND_01")
    if handler["cups"] != 8:
        raise RuntimeError(f"Handling EOAT has {handler['cups']} contacts, expected 8")
    old_active_tool_markers = (
        "/Game/LineBoss/Candidates/WeldShop/Robots/WeldRobotRuntime_v001/",
        "SM_LB_WeldTool_SpotGun_v001",
    )
    active_tool_paths = {
        row["tool_mesh"] for row in rows
    }
    if any(
        marker in path
        for path in active_tool_paths
        for marker in old_active_tool_markers
    ):
        raise RuntimeError(
            "Legacy WeldRobotRuntime/SpotGun remained active in the Body Shop robot set"
        )
    spot = {
        row["slot"]
        for row in rows
        if row["tool_mesh"] == EXPECTED_NATIVE_OPEN_CGUN
    }
    if spot != EXPECTED_SPOT_SLOTS:
        raise RuntimeError(f"Expected two authored spot/C-gun bindings, found {sorted(spot)}")
    if not bool(pawns[0].focus_prototype_process()):
        raise RuntimeError("Actual LBBodyShopManagementPawn did not frame commissioned process bounds")
    payload["checks"]["runtime_actual_player_contract"] = {
        "passed": True, "counts": counts, "definitions": sorted(definitions),
        "robots": rows, "native_open_cgun_slots": sorted(spot),
        "management_zoom_cm": float(pawns[0].get_prototype_zoom_distance()),
        "pawn_class": pawns[0].get_class().get_name(), "hud_class": huds[0].get_class().get_name(),
        "player_possessed": True, "player_hud_active": True,
        "umg_operator_shell_active": True, "canvas_overlay_required": False,
    }
    return runtime[0], authority[0], cells, robots, pawns[0]


def placement_contract(world, authority):
    # Validate an accepted and rejected 90-degree transform without mutating the six-cell graph.
    cells_before = len(actors_of(world, unreal.LBBodyShopCellActor))
    valid_transform = unreal.Transform(location=unreal.Vector(0.0, 1000.0, 0.0),
                                       rotation=unreal.Rotator(roll=0.0, pitch=0.0, yaw=90.0),
                                       scale=unreal.Vector(1.0, 1.0, 1.0))
    invalid_rotation = unreal.Transform(location=unreal.Vector(0.0, 1000.0, 0.0),
                                        rotation=unreal.Rotator(roll=0.0, pitch=0.0, yaw=45.0),
                                        scale=unreal.Vector(1.0, 1.0, 1.0))
    invalid_grid = unreal.Transform(location=unreal.Vector(50.0, 1050.0, 0.0),
                                    rotation=unreal.Rotator(roll=0.0, pitch=0.0, yaw=90.0),
                                    scale=unreal.Vector(1.0, 1.0, 1.0))
    definition = unreal.Name("BW014_OUTPUT_BUFFER_BASIC")
    method = getattr(authority, "validate_module_placement_for_validation", None)
    if method is None:
        raise RuntimeError(
            "PLACEMENT_VALIDATION_SEAM_MISSING: expose a non-mutating BlueprintCallable "
            "ALBBodyShopBuildAuthority::ValidateModulePlacementForValidation wrapper; the existing "
            "ValidateModulePlacement method is intentionally plain C++ and cannot be called by UE Python"
        )
    def unpack(value):
        if not isinstance(value, tuple) or len(value) != 2:
            raise RuntimeError(f"Unexpected reflected placement result: {value!r}")
        return bool(value[0]), str(value[1])
    accepted = method(definition, valid_transform)
    rejected_rotation = method(definition, invalid_rotation)
    rejected_grid = method(definition, invalid_grid)
    accepted_ok, accepted_reason = unpack(accepted)
    rotation_ok, rotation_reason = unpack(rejected_rotation)
    grid_ok, grid_reason = unpack(rejected_grid)
    cells_after = len(actors_of(world, unreal.LBBodyShopCellActor))
    if not accepted_ok or rotation_ok or grid_ok or cells_before != cells_after:
        raise RuntimeError("Placement validation did not independently enforce 100 cm snap and 90-degree rotation without mutation")
    payload["checks"]["placement_rotation_non_mutating"] = {
        "passed": True, "method": "ValidateModulePlacementForValidation",
        "graph_actor_count_before": cells_before, "graph_actor_count_after": cells_after,
        "accepted": {"location_cm": [0, 1000, 0], "yaw_degrees": 90, "reason": accepted_reason},
        "rejected_rotation": {"location_cm": [0, 1000, 0], "yaw_degrees": 45, "reason": rotation_reason},
        "rejected_grid": {"location_cm": [50, 1050, 0], "yaw_degrees": 90, "reason": grid_reason},
    }


def sample_joints(runtime, robots):
    global last_joint_sample
    now = time.monotonic()
    if now - last_joint_sample < 0.20:
        return
    last_joint_sample = now
    stage = enum_text(runtime.get_runtime_stage())
    rows = []
    moved = False
    for robot in robots:
        slot = str(robot.get_slot_id())
        angles = [round(float(robot.get_joint_angle_degrees(index)), 3) for index in range(6)]
        if slot not in home_angles:
            home_angles[slot] = angles
        delta = max(abs(a - b) for a, b in zip(angles, home_angles[slot]))
        moved = moved or delta > 0.25
        rows.append({"slot": slot, "pose": enum_text(robot.get_current_pose()),
                     "target_pose": enum_text(robot.get_target_pose()), "joint_degrees": angles,
                     "max_delta_from_home_degrees": round(delta, 3)})
    if stage not in sampled_stages or moved:
        payload["stage_joint_samples"].append({"elapsed_seconds": round(now - started, 3),
                                                "stage": stage, "robots": rows})
        sampled_stages.add(stage)


def welding_process_receipt(runtime, robots):
    by_slot = {str(robot.get_slot_id()): robot for robot in robots}
    if not EXPECTED_SPOT_SLOTS.issubset(by_slot):
        return {"passed": False, "stage": enum_text(runtime.get_runtime_stage()),
                "reason": "Both authored spot-weld robot slots were not present"}
    rows = {}
    for slot in sorted(EXPECTED_SPOT_SLOTS):
        robot = by_slot[slot]
        gun_tip = robot.get_weld_gun_presentation_tip_location()
        gun_approach = robot.get_weld_gun_presentation_approach_direction()
        rows[slot] = {
            "pose": enum_text(robot.get_current_pose()),
            "target_pose": enum_text(robot.get_target_pose()),
            "work_pose_index": int(robot.get_current_weld_work_pose_index()),
            "articulation_running": bool(robot.is_articulation_running()),
            "joint_degrees": [round(float(robot.get_joint_angle_degrees(index)), 3)
                              for index in range(6)],
            "gun_tip_world_cm": [round(float(gun_tip.x), 3),
                                 round(float(gun_tip.y), 3),
                                 round(float(gun_tip.z), 3)],
            "gun_approach_world": [round(float(gun_approach.x), 6),
                                   round(float(gun_approach.y), 6),
                                   round(float(gun_approach.z), 6)],
        }
    left = rows["ROBOT_WELD_LEFT"]["joint_degrees"]
    right = rows["ROBOT_WELD_RIGHT"]["joint_degrees"]
    mirrored = {
        "j1_opposite": math.isclose(left[0], -right[0], rel_tol=0.0, abs_tol=0.05),
        "j2_equal": math.isclose(left[1], right[1], rel_tol=0.0, abs_tol=0.05),
        "j3_equal": math.isclose(left[2], right[2], rel_tol=0.0, abs_tol=0.05),
        "j4_opposite": math.isclose(left[3], -right[3], rel_tol=0.0, abs_tol=0.05),
        "j5_equal": math.isclose(left[4], right[4], rel_tol=0.0, abs_tol=0.05),
        "j6_opposite": math.isclose(left[5], -right[5], rel_tol=0.0, abs_tol=0.05),
    }
    both_process = all(row["pose"] == "PROCESS" and row["target_pose"] == "PROCESS"
                       for row in rows.values())
    work_pose_indices = {row["work_pose_index"] for row in rows.values()}
    synchronised_work_pose = (len(work_pose_indices) == 1
                              and next(iter(work_pose_indices)) in {0, 1, 2})
    visibly_articulated = all(max(abs(value) for value in row["joint_degrees"]) > 0.25
                              for row in rows.values())
    return {
        "passed": (enum_text(runtime.get_runtime_stage()) == "WELDING_UNDERBODY"
                   and both_process and synchronised_work_pose
                   and visibly_articulated and all(mirrored.values())),
        "stage": enum_text(runtime.get_runtime_stage()),
        "both_current_and_target_process": both_process,
        "synchronised_authored_work_pose": synchronised_work_pose,
        "visibly_articulated": visibly_articulated,
        "mirrored_joint_contract": mirrored,
        "robots": rows,
    }


def screenshot_file_ready(path):
    return path is not None and path.exists() and path.stat().st_size >= 1024


def request_perf_evidence(world):
    if len(payload["screenshots"]) < 6 or not all(
            screenshot_file_ready(Path(shot["path"])) for shot in payload["screenshots"]):
        raise RuntimeError("Performance stats cannot be enabled before all visual evidence is complete")
    commands = ["stat unit", "stat gpu", "stat memory", "stat streaming", "stat scenerendering", "stat rhi"]
    for command in commands:
        unreal.SystemLibrary.execute_console_command(world, command)
    payload["checks"]["performance_evidence_requested"] = {
        "passed": True, "commands": commands,
        "visual_captures_complete_before_commands": True,
        "visual_capture_count_before_commands": len(payload["screenshots"]),
        "log_capture_requested": "run_body_shop_release_validation_v001.ps1 retains Unreal stdout log",
        "numeric_budget_gate": False,
    }


def take_player_screenshot(world, filename):
    # No camera argument: capture the possessed LBBodyShopManagementPawn scene.
    # AutomationLibrary's high-res path does not composite Slate, so each view
    # also requests a native viewport SHOT SHOWUI below.
    output = CAPTURE_DIR / filename
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    task = unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, str(output),
                                                             force_game_view=False)
    if not task.is_valid_task():
        raise RuntimeError(f"Invalid player screenshot task for {filename}")
    payload["screenshots"].append({"path": str(output), "source": "possessed_management_pawn",
                                   "hud_required": False})
    return task


def request_player_ui_screenshot(world, filename):
    output = CAPTURE_DIR / filename
    # UE 5.8's viewport SHOT command appends its deterministic first-shot
    # sequence even when NOSUFFIX is supplied. Each validation run has a fresh
    # directory, so the actual Slate-composited file is always *00000.png.
    actual_output = output.with_name(f"{output.stem}00000{output.suffix}")
    command = f'SHOT SHOWUI filename="{str(output).replace(chr(92), "/")}" nosuffix'
    unreal.SystemLibrary.execute_console_command(world, command)
    payload["screenshots"].append({"path": str(actual_output),
                                   "source": "possessed_management_pawn_slate_ui",
                                   "hud_required": True})
    return actual_output


def finish(status, detail=""):
    global tick_handle
    payload["status"] = status
    payload["detail"] = detail
    payload["finished_utc"] = datetime.now(timezone.utc).isoformat()
    payload["map_sha256_after"] = hashlib.sha256(MAP_FILE.read_bytes()).hexdigest().upper()
    payload["map_hash_unchanged"] = payload["map_sha256_after"] == MAP_SHA_BEFORE
    payload["full_restored_press_sha256_after"] = hashlib.sha256(
        RESTORED_PRESS_FILE.read_bytes()
    ).hexdigest().upper()
    payload["full_restored_press_hash_unchanged"] = (
        payload["full_restored_press_sha256_after"]
        == EXPECTED_RESTORED_PRESS_SHA256
    )
    for shot in payload["screenshots"]:
        path = Path(shot["path"])
        shot["exists"] = path.exists() and path.stat().st_size >= 1024
        shot["bytes"] = path.stat().st_size if path.exists() else 0
        shot["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest().upper() if shot["exists"] else None
    if not payload["map_hash_unchanged"]:
        payload["failures"].append("Saved Body Shop map hash changed")
    if not payload["full_restored_press_hash_unchanged"]:
        payload["failures"].append("Full restored Press map hash changed")
    try:
        support_after = validate_support_kit(ROOT)
        payload["native_support_kit_v002_after"] = support_after
        payload["native_support_kit_v002_unchanged"] = (
            support_after == FINAL_NATIVE_SUPPORT_KIT)
        if not payload["native_support_kit_v002_unchanged"]:
            payload["failures"].append("Native support-kit v002 changed during PIE")
    except Exception as exc:
        payload["native_support_kit_v002_unchanged"] = False
        payload["failures"].append(
            "Native support-kit v002 post-PIE validation failed: " + str(exc))
    if not all(shot["exists"] for shot in payload["screenshots"]):
        payload["failures"].append("One or more actual-player evidence screenshots are missing")
    moved_stages = [sample for sample in payload["stage_joint_samples"]
                    if any(row["max_delta_from_home_degrees"] > 0.25 for row in sample["robots"])]
    if not moved_stages:
        payload["failures"].append("No non-HOME robot joint transform was sampled")
    required = ("runtime_actual_player_contract", "underbody_release_presentation_contract",
                "native_support_service_dressing_v002",
                "placement_rotation_non_mutating",
                "welding_process_mirrored_sample", "quality_pass", "blocked_output",
                "save_reload_one_logical_visible_wip", "starvation", "quality_fail")
    missing = [name for name in required if not payload["checks"].get(name, {}).get("passed")]
    if missing:
        payload["failures"].append("Missing required runtime checks: " + ", ".join(missing))
    if payload["failures"]:
        payload["status"] = "FAIL__BODY_SHOP_RELEASE_CANDIDATE_LIVE_PIE"
    AUDIT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    try:
        LEVELS.editor_request_end_play()
    finally:
        unreal.SystemLibrary.quit_editor()


def fail(message):
    unreal.log_error("LINE_BOSS_BODY_SHOP_RELEASE_PIE_FAIL " + message)
    payload["failures"].append(message)
    finish("FAIL__BODY_SHOP_RELEASE_CANDIDATE_LIVE_PIE", message)


def tick(_delta_seconds):
    global phase, phase_started, capture_task, ui_capture_path
    global welding_capture_world_time_marker
    global welding_pre_camera_skid_render_time, welding_pre_camera_underbody_render_time
    now = time.monotonic()
    if now - started > 145.0:
        fail("Timed out in phase " + phase)
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    try:
        runtimes = actors_of(world, unreal.LBBodyShopPrototypeRuntime)
        robots = actors_of(world, unreal.LBBodyShopRobotActor)
        if runtimes and robots:
            sample_joints(runtimes[0], robots)

        if phase == "wait_world":
            if now - phase_started < 4.0:
                return
            runtime, authority, _cells, robots, pawn = actor_contract(world)
            placement_contract(world, authority)
            phase = "capturing_overview"
            phase_started = now
            capture_task = take_player_screenshot(world, "01_actual_management_pawn_hud_overview.png")
            phase = "wait_overview"
            return

        if phase == "wait_overview":
            if not capture_task.is_task_done() or now - phase_started < 2.0:
                return
            ui_capture_path = request_player_ui_screenshot(
                world, "01_actual_management_pawn_hud_overview_with_ui.png")
            phase = "wait_overview_ui"
            phase_started = now
            return

        if phase == "wait_overview_ui":
            if now - phase_started < 1.0 or not screenshot_file_ready(ui_capture_path):
                return
            runtime = runtimes[0]
            success, evidence = start_cycle(runtime)
            payload["checks"]["start_quality_pass_cycle"] = {"passed": success, **evidence}
            if not success:
                raise RuntimeError("Could not start quality-pass pilot cycle")
            phase = "wait_welding_process"
            phase_started = now
            return

        if phase == "wait_welding_process":
            runtime = runtimes[0]
            stage = enum_text(runtime.get_runtime_stage())
            if stage == "WELDING_UNDERBODY":
                receipt = welding_process_receipt(runtime, robots)
                if not receipt["passed"]:
                    return
                paused, pause_reason = call_bool_with_reason(
                    lambda: runtime.set_simulation_running(False))
                if not paused or bool(runtime.is_simulation_running()):
                    raise RuntimeError(
                        "Could not pause Body Shop simulation for deterministic welding evidence: "
                        + pause_reason)
                running_articulation = int(runtime.get_running_robot_articulation_count())
                if running_articulation != 0 or any(
                        bool(robot.is_articulation_running()) for robot in robots):
                    raise RuntimeError(
                        "Body Shop simulation pause did not freeze all authored robot articulation")
                receipt["runtime_simulation_paused_for_deterministic_capture"] = True
                receipt["running_robot_articulation_count_after_pause"] = running_articulation
                payload["checks"]["welding_process_mirrored_sample"] = receipt
                welding_pre_camera_skid_render_time = float(
                    runtime.get_pilot_skid_last_render_time_on_screen_seconds())
                welding_pre_camera_underbody_render_time = float(
                    runtime.get_pilot_underbody_last_render_time_on_screen_seconds())
                pawn = actors_of(world, unreal.LBBodyShopManagementPawn)[0]
                pawn.set_actor_location(unreal.Vector(-4500.0, -1800.0, 180.0), False, False)
                pawn.set_prototype_zoom_input(1.5)
                welding_capture_world_time_marker = float(
                    unreal.GameplayStatics.get_time_seconds(world))
                payload["checks"]["welding_process_mirrored_sample"][
                    "capture_camera_placed_world_time_seconds"] = round(
                        welding_capture_world_time_marker, 6)
                phase = "capturing_welding_process"
                phase_started = now
                return
            if stage in {"CONVEYING_SKID", "INSPECTING", "COMPLETE"}:
                raise RuntimeError("Welding stage ended before both spot robots reached mirrored PROCESS")
            return

        if phase == "capturing_welding_process":
            receipt = welding_process_receipt(runtimes[0], robots)
            if not receipt["passed"] or bool(runtimes[0].is_simulation_running()):
                raise RuntimeError("Welding PROCESS pose was not held for deterministic capture")
            capture_task = take_player_screenshot(
                world, "03_actual_management_pawn_welding_process_view.png")
            phase = "wait_welding_high_res"
            phase_started = now
            return

        if phase == "wait_welding_high_res":
            if not capture_task.is_task_done() or now - phase_started < 2.0:
                return
            ui_capture_path = request_player_ui_screenshot(
                world, "03_actual_management_pawn_welding_process_view_with_ui.png")
            phase = "wait_welding_ui"
            phase_started = now
            return

        if phase == "wait_welding_ui":
            if now - phase_started < 1.0 or not screenshot_file_ready(ui_capture_path):
                return
            runtime = runtimes[0]
            receipt = welding_process_receipt(runtime, robots)
            if not receipt["passed"] or bool(runtime.is_simulation_running()):
                raise RuntimeError("Welding PROCESS pose changed before both captures completed")
            start_rows = payload["checks"]["welding_process_mirrored_sample"]["robots"]
            held_rows = receipt["robots"]
            joint_arrays_held = all(
                all(math.isclose(float(before), float(after), rel_tol=0.0, abs_tol=0.01)
                    for before, after in zip(start_rows[slot]["joint_degrees"],
                                             held_rows[slot]["joint_degrees"]))
                for slot in EXPECTED_SPOT_SLOTS)
            articulation_still_frozen = (
                int(runtime.get_running_robot_articulation_count()) == 0
                and not any(bool(robot.is_articulation_running()) for robot in robots))
            skid_min = runtime.get_pilot_skid_presentation_world_bounds_min()
            skid_max = runtime.get_pilot_skid_presentation_world_bounds_max()
            underbody_min = runtime.get_pilot_underbody_presentation_world_bounds_min()
            underbody_max = runtime.get_pilot_underbody_presentation_world_bounds_max()
            skid_last_render_time = float(
                runtime.get_pilot_skid_last_render_time_on_screen_seconds())
            underbody_last_render_time = float(
                runtime.get_pilot_underbody_last_render_time_on_screen_seconds())
            render_evidence = {
                "skid_mesh_path": str(runtime.get_pilot_skid_presentation_mesh_path()),
                "underbody_mesh_path": str(
                    runtime.get_pilot_underbody_presentation_mesh_path()),
                "skid_visible_and_owner_unhidden": bool(
                    runtime.is_pilot_skid_presentation_visible_and_unhidden()),
                "underbody_visible_and_owner_unhidden": bool(
                    runtime.is_pilot_underbody_presentation_visible_and_unhidden()),
                "aligned_in_weld_fixture": bool(
                    runtime.is_skid_underbody_presentation_aligned_in_weld_fixture()),
                "skid_recently_rendered": bool(
                    runtime.was_pilot_skid_presentation_recently_rendered(3.0)),
                "underbody_recently_rendered": bool(
                    runtime.was_pilot_underbody_presentation_recently_rendered(3.0)),
                "combined_recently_rendered": bool(
                    runtime.was_skid_underbody_presentation_recently_rendered(3.0)),
                "camera_placed_world_time_seconds": round(
                    float(welding_capture_world_time_marker or 0.0), 6),
                "skid_pre_camera_last_render_time_on_screen_seconds": round(
                    float(welding_pre_camera_skid_render_time or 0.0), 6),
                "underbody_pre_camera_last_render_time_on_screen_seconds": round(
                    float(welding_pre_camera_underbody_render_time or 0.0), 6),
                "skid_last_render_time_on_screen_seconds": round(
                    skid_last_render_time, 6),
                "underbody_last_render_time_on_screen_seconds": round(
                    underbody_last_render_time, 6),
                "robot_joint_arrays_held_across_both_captures": joint_arrays_held,
                "robot_articulation_still_frozen_after_both_captures": (
                    articulation_still_frozen),
                "skid_world_bounds_cm": {
                    "min": [round(float(skid_min.x), 3), round(float(skid_min.y), 3),
                            round(float(skid_min.z), 3)],
                    "max": [round(float(skid_max.x), 3), round(float(skid_max.y), 3),
                            round(float(skid_max.z), 3)],
                },
                "underbody_world_bounds_cm": {
                    "min": [round(float(underbody_min.x), 3),
                            round(float(underbody_min.y), 3),
                            round(float(underbody_min.z), 3)],
                    "max": [round(float(underbody_max.x), 3),
                            round(float(underbody_max.y), 3),
                            round(float(underbody_max.z), 3)],
                },
            }
            render_evidence["both_rendered_after_welding_camera_placement"] = (
                welding_capture_world_time_marker is not None
                and welding_pre_camera_skid_render_time is not None
                and welding_pre_camera_underbody_render_time is not None
                and skid_last_render_time > welding_pre_camera_skid_render_time + 0.000001
                and underbody_last_render_time
                    > welding_pre_camera_underbody_render_time + 0.000001
                and skid_last_render_time >= welding_capture_world_time_marker - 0.001
                and underbody_last_render_time
                    >= welding_capture_world_time_marker - 0.001)
            render_evidence["passed"] = (
                render_evidence["skid_mesh_path"] == EXPECTED_PILOT_SKID_MESH
                and render_evidence["underbody_mesh_path"] == EXPECTED_PILOT_UNDERBODY_MESH
                and render_evidence["skid_visible_and_owner_unhidden"]
                and render_evidence["underbody_visible_and_owner_unhidden"]
                and render_evidence["aligned_in_weld_fixture"]
                and render_evidence["skid_recently_rendered"]
                and render_evidence["underbody_recently_rendered"]
                and render_evidence["combined_recently_rendered"]
                and render_evidence["both_rendered_after_welding_camera_placement"]
                and render_evidence["robot_joint_arrays_held_across_both_captures"]
                and render_evidence["robot_articulation_still_frozen_after_both_captures"])
            payload["checks"]["welding_process_mirrored_sample"][
                "skid_underbody_render_evidence"] = render_evidence
            if not render_evidence["passed"]:
                raise RuntimeError(
                    "Welding screenshots did not prove the approved skid and underbody rendered")
            payload["checks"]["welding_process_mirrored_sample"][
                "both_captures_completed_in_held_process_stage"] = True
            pawn = actors_of(world, unreal.LBBodyShopManagementPawn)[0]
            if not bool(pawn.focus_prototype_process()):
                raise RuntimeError("Could not restore management overview after welding capture")
            resumed, resume_reason = call_bool_with_reason(
                lambda: runtime.set_simulation_running(True))
            if not resumed or not bool(runtime.is_simulation_running()):
                raise RuntimeError(
                    "Could not resume Body Shop simulation after deterministic welding evidence: "
                    + resume_reason)
            if int(runtime.get_running_robot_articulation_count()) != int(
                    runtime.get_spawned_robot_count()):
                raise RuntimeError(
                    "Body Shop simulation resume did not restore all robot articulation")
            phase = "wait_quality_pass"
            phase_started = now
            return

        if phase == "wait_quality_pass":
            runtime = runtimes[0]
            if enum_text(runtime.get_runtime_stage()) != "COMPLETE":
                return
            payload["checks"]["quality_pass"] = {
                "passed": (int(runtime.get_active_pilot_wip_count()) == 1
                           and int(runtime.get_visible_runtime_wip_presentation_count()) == 1),
                "stage": enum_text(runtime.get_runtime_stage()),
                "logical_wip": int(runtime.get_active_pilot_wip_count()),
                "logical_visible_assembly_count": int(runtime.get_visible_runtime_wip_presentation_count()),
            }
            ok, reason = call_bool_with_reason(runtime.clear_held_pilot_unit_for_validation)
            if not ok:
                raise RuntimeError("Could not clear completed quality-pass unit: " + reason)
            runtime.set_output_buffer_blocked_for_validation(True)
            success, evidence = start_cycle(runtime)
            if not success:
                raise RuntimeError("Could not start blocked-output pilot cycle")
            phase = "wait_blocked"
            phase_started = now
            return

        if phase == "wait_blocked":
            runtime = runtimes[0]
            if enum_text(runtime.get_runtime_stage()) != "OUTPUT_BLOCKED":
                return
            logical_before = int(runtime.get_active_pilot_wip_count())
            visible_before = int(runtime.get_visible_runtime_wip_presentation_count())
            payload["checks"]["blocked_output"] = {"passed": logical_before == 1 and visible_before == 1,
                                                           "logical_wip": logical_before,
                                                           "logical_visible_assembly_count": visible_before}
            ok, save_reason = call_bool_with_reason(runtime.save_to_experimental_slot)
            if not ok:
                raise RuntimeError("Experimental save failed: " + save_reason)
            ok, load_reason = call_bool_with_reason(runtime.load_from_experimental_slot)
            logical_after = int(runtime.get_active_pilot_wip_count())
            visible_after = int(runtime.get_visible_runtime_wip_presentation_count())
            payload["checks"]["save_reload_one_logical_visible_wip"] = {
                "passed": ok and logical_before == logical_after == 1 and visible_before == visible_after == 1,
                "logical_before": logical_before, "logical_after": logical_after,
                "logical_visible_assembly_count_before": visible_before,
                "logical_visible_assembly_count_after": visible_after,
                "save_reason": save_reason, "load_reason": load_reason,
            }
            if not payload["checks"]["save_reload_one_logical_visible_wip"]["passed"]:
                raise RuntimeError("Save/reload duplicated or lost logical/visible WIP")
            payload["checks"]["underbody_release_presentation_contract"][
                "fixture_capture_runtime_wip"] = {
                    "passed": logical_after == visible_after == 1,
                    "logical_wip_before_captures": logical_after,
                    "visible_runtime_wip_before_captures": visible_after,
                    "both_captures_completed_with_one_runtime_wip": False,
                }
            # Focus the real pawn tighter for the fixture image; no transient camera or saved mutation.
            pawn = actors_of(world, unreal.LBBodyShopManagementPawn)[0]
            pawn.set_actor_location(unreal.Vector(-4500.0, -1800.0, 180.0), False, False)
            pawn.set_prototype_zoom_input(1.5)
            phase = "capturing_fixture"
            phase_started = now
            capture_task = take_player_screenshot(world, "02_actual_management_pawn_fixture_view.png")
            phase = "wait_fixture"
            return

        if phase == "wait_fixture":
            if not capture_task.is_task_done() or now - phase_started < 2.0:
                return
            ui_capture_path = request_player_ui_screenshot(
                world, "02_actual_management_pawn_fixture_view_with_ui.png")
            phase = "wait_fixture_ui"
            phase_started = now
            return

        if phase == "wait_fixture_ui":
            if now - phase_started < 1.0 or not screenshot_file_ready(ui_capture_path):
                return
            runtime = runtimes[0]
            logical_after_captures = int(runtime.get_active_pilot_wip_count())
            visible_after_captures = int(runtime.get_visible_runtime_wip_presentation_count())
            fixture_wip = payload["checks"]["underbody_release_presentation_contract"][
                "fixture_capture_runtime_wip"]
            fixture_wip.update({
                "logical_wip_after_both_captures": logical_after_captures,
                "visible_runtime_wip_after_both_captures": visible_after_captures,
                "both_captures_completed_with_one_runtime_wip": (
                    logical_after_captures == visible_after_captures == 1),
            })
            fixture_wip["passed"] = (
                fixture_wip["passed"]
                and fixture_wip["both_captures_completed_with_one_runtime_wip"])
            if not fixture_wip["passed"]:
                raise RuntimeError(
                    "Fixture captures did not retain exactly one logical and visible runtime WIP")
            request_perf_evidence(world)
            runtime.set_output_buffer_blocked_for_validation(False)
            if enum_text(runtime.get_runtime_stage()) != "COMPLETE":
                raise RuntimeError("Unblocking the output did not release the held unit to Complete")
            ok, reason = call_bool_with_reason(runtime.clear_held_pilot_unit_for_validation)
            if not ok:
                raise RuntimeError("Could not clear blocked unit: " + reason)
            runtime.set_pilot_stillage_available(False)
            success, evidence = start_cycle(runtime)
            stage = enum_text(runtime.get_runtime_stage())
            payload["checks"]["starvation"] = {"passed": (not success and stage == "AWAITING_PANEL_STILLAGE"),
                                                       "stage": stage, **evidence}
            if not payload["checks"]["starvation"]["passed"]:
                raise RuntimeError("Expected empty-stillage starvation")
            runtime.set_pilot_stillage_available(True)
            runtime.set_next_vision_result_for_validation(False)
            success, evidence = start_cycle(runtime)
            if not success:
                raise RuntimeError("Could not start quality-fail pilot cycle")
            phase = "wait_quality_fail"
            phase_started = now
            return

        if phase == "wait_quality_fail":
            runtime = runtimes[0]
            if enum_text(runtime.get_runtime_stage()) != "QUALITY_HOLD":
                return
            logical = int(runtime.get_active_pilot_wip_count())
            visible = int(runtime.get_visible_runtime_wip_presentation_count())
            payload["checks"]["quality_fail"] = {"passed": logical == 1 and visible == 1,
                                                         "logical_wip": logical,
                                                         "logical_visible_assembly_count": visible,
                                                         "stage": enum_text(runtime.get_runtime_stage())}
            finish("PASS__BODY_SHOP_RELEASE_CANDIDATE_ACTUAL_PLAYER_PIE")
    except Exception as exc:
        fail(str(exc))


if not MAP_FILE.exists():
    raise RuntimeError(f"Missing Body Shop map: {MAP_FILE}")
if not LEVELS.load_level(MAP):
    raise RuntimeError(f"Could not load isolated Body Shop map: {MAP}")
LEVELS.editor_request_begin_play()
tick_handle = unreal.register_slate_post_tick_callback(tick)
