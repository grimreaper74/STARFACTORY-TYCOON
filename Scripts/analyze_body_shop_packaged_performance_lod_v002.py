"""Fail-closed packaged-Development 1080p performance and renderer-LOD gate.

The two runtime receipts are emitted by token-gated non-Shipping game processes.
This analyzer binds them to the exact PASS Development package, executable,
engine logs, 300-frame CSV profiles and game-thread renderer LOD snapshots before
applying the same numeric budgets as the retired editor-PIE v1 lane.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import sys

import analyze_body_shop_performance_lod_v001 as legacy
from body_shop_support_kit_native_v002_contract import (
    ContractError as SupportKitContractError,
    validate as validate_support_kit,
)


PACKAGE_SCHEMA = "cairnwell/body-shop/experimental-v001/development-package-run/v2"
PACKAGE_STATUS = "PASS__BODY_SHOP_DEVELOPMENT_PACKAGE_TWO_PROCESS_V002"
RUNTIME_SCHEMA = "cairnwell/body-shop/experimental-v001/packaged-performance-runtime-view/v2"
RUNTIME_STATUS = "PASS__BODY_SHOP_PACKAGED_PERFORMANCE_LOD_VIEW_V002"
PASS_STATUS = "PASS__BODY_SHOP_PACKAGED_NUMERIC_PERFORMANCE_AND_RENDERER_LOD_GATE_V002"
FAIL_STATUS = "FAIL__BODY_SHOP_PACKAGED_NUMERIC_PERFORMANCE_AND_RENDERER_LOD_GATE_V002"
MAP = "/Game/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001"
EXPECTED_COMPONENTS = 25
EXPECTED_DEFAULT_GAME_SHA256 = "4458BB41EE3A56B67B8ECDD6954A46B23FD038A9CB8294E9A79C48580A86852B"
NATIVE_ROBOT_SCHEMA = "lineboss/audit/bodyshop-robot-native-v001-fresh-load-validation/v1"
NATIVE_ROBOT_STATUS = (
    "PASS__INDEPENDENT_FRESH_PROCESS_LOAD__INCIDENT_ARCHIVE_VERIFIED__"
    "8_ASSETS_3_LODS_MONOTONIC_ONE_UV_BODYSHOP_ROBOT_NATIVE_V001"
)
NATIVE_ROBOT_BASELINE_SHA256 = (
    "D967E8CD1596FC620066668138FEE14A47C702D55989FB1DB1C3AAF0ABF0FF31"
)
NATIVE_ROBOT_CLEAN_DISPOSITION_CONTRACT_SHA256 = (
    "E9862B44C656586879EF3607C33BD8A536E9CE0D816C144AFF870C31A7B52BC3"
)
NATIVE_ROBOT_LANE_SUMMARY_SHA256 = "B1AFEDB019C28B04082497F46B954C29262D0A30B19854D00CF1168537AA2F73"
NATIVE_ROBOT_IMPORT_RECEIPT_SHA256 = "B7738C068F344BBA391442F404E38A87BAF0C70B72A19CD2CA5DDDC68A5210BF"
NATIVE_ROBOT_VALIDATION_RECEIPT_SHA256 = "9A4097CBB68F46297031A092FF861B20FC4B2F60576150005B483D984E26EBEA"
NATIVE_ROBOT_TRIANGLE_TOTALS = [2628, 1964, 1356]
NATIVE_ROBOT_NAMESPACE = "/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001"
EXPECTED_NATIVE_PACKAGES = {
    "Base": NATIVE_ROBOT_NAMESPACE + "/Robot/SM_LB_BodyShopRobotNative_Base_v001",
    **{
        f"J{joint}": (
            NATIVE_ROBOT_NAMESPACE
            + f"/Robot/SM_LB_BodyShopRobotNative_J{joint}_v001"
        )
        for joint in range(1, 7)
    },
    "CGun": NATIVE_ROBOT_NAMESPACE + "/Tools/SM_LB_BodyShopToolNative_OpenCGun_v001",
}
EXPECTED_NATIVE_PACKAGE_HASHES = {
    "Base": "EB7975C71866AD9531FE8EBA93CAA14EDE06CC4333CCFBF88F965DF5E52E7000",
    "CGun": "7473FA6260B17333ABC5D2833736A657D093458CFA004DD862876096F407EFE1",
    "J1": "50C2A7065808D59C6666D52CC44F4BDB045E0B929350D9F821E5DEF027AE54C7",
    "J2": "E6D5FA37E12B14279FE23042C940B3EF2FB33F3D6EE9D7E0D659526F5A471230",
    "J3": "02D873DD7E6688AC60DD2E4D367A78742D6524CEDF80CABA876E20FD5B2D44C5",
    "J4": "A9F887F6B8FF3955CD48FA3BF132F6F24A00DAED1765194442AD7999048E997C",
    "J5": "EE26BCDD02B6F43132B5C2CCDB8F216B01CEDFA163748E8AC05A0CF5397D116F",
    "J6": "832AC4BAD232E5BDBC1675A1E46B64BDFA4A833C5CAF1B4478A8E9492BBA0D10",
}
EXPECTED_MESHES = {
    "/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_Base_v001.SM_LB_BodyShopRobotNative_Base_v001",
    "/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J1_v001.SM_LB_BodyShopRobotNative_J1_v001",
    "/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J2_v001.SM_LB_BodyShopRobotNative_J2_v001",
    "/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J3_v001.SM_LB_BodyShopRobotNative_J3_v001",
    "/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J4_v001.SM_LB_BodyShopRobotNative_J4_v001",
    "/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J5_v001.SM_LB_BodyShopRobotNative_J5_v001",
    "/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J6_v001.SM_LB_BodyShopRobotNative_J6_v001",
    "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Tools/SM_LB_BodyShopTool_PanelPick8Cup_v001.SM_LB_BodyShopTool_PanelPick8Cup_v001",
    "/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Tools/SM_LB_BodyShopToolNative_OpenCGun_v001.SM_LB_BodyShopToolNative_OpenCGun_v001",
    "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Vision/SM_LB_BodyShop_VisionGate_v001.SM_LB_BodyShop_VisionGate_v001",
}
EXPECTED_MARKER = re.compile(
    r"^LINE_BOSS_BODY_SHOP_PACKAGED_PERFORMANCE_LOD_V002 "
    r"view=(MANAGEMENT|FOCUS) token=([A-Za-z0-9_-]{16,96}) result=PASS "
    r"viewport=1920x1080 frames=300 components=25 meshes=10 "
    r"rhi=([A-Za-z0-9_.-]+) receipt=([A-Za-z0-9_.-]+)$"
)
FORBIDDEN_LOG = re.compile(
    r"Fatal error|Unhandled Exception|Assertion failed|Ensure condition failed",
    re.IGNORECASE,
)
PACKAGED_BUDGETS = deepcopy(legacy.BUDGETS)
PACKAGED_BUDGETS["basis"] = (
    "Provisional Windows desktop packaged Development gate at an exact "
    "1920x1080 real-RHI game viewport; not a Shipping-platform commitment."
)
PACKAGED_BUDGETS["scene_measurement_authority"] = {
    "visible_primitives": "registered scene-proxy component upper bound",
    "draw_calls": "300-frame CSV RHI draw-calls p95",
    "triangles": "300-frame CSV RHI primitives-drawn p95",
}


class GateFailure(RuntimeError):
    pass


def sha256(path: Path) -> str:
    return legacy.sha256(path)


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def require_file(path: Path, label: str, minimum_bytes: int = 1) -> Path:
    resolved = path.resolve()
    if not resolved.is_file() or resolved.stat().st_size < minimum_bytes:
        raise GateFailure(f"{label} is missing or too small: {resolved}")
    return resolved


def hash_record(path: Path) -> dict:
    path = require_file(path, "Hash-bound evidence")
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def validate_body_shop_source_contract(package: dict) -> list[dict]:
    snapshots = []
    for phase in ("protected_before", "protected_after"):
        rows = package.get(phase, {}).get("all_body_shop_source")
        if not isinstance(rows, list) or not rows:
            raise GateFailure(f"Development package has no {phase} Body Shop source snapshot")
        bound = {}
        for row in rows:
            if not isinstance(row, dict):
                raise GateFailure(f"Development package {phase} source row is invalid")
            path = require_file(Path(str(row.get("path", ""))), f"{phase} Body Shop source")
            expected_hash = str(row.get("sha256", ""))
            if not re.fullmatch(r"[0-9A-F]{64}", expected_hash):
                raise GateFailure(f"Development package {phase} source hash is invalid: {path}")
            key = str(path).lower()
            if key in bound or sha256(path) != expected_hash:
                raise GateFailure(f"Development package {phase} source hash drifted: {path}")
            bound[key] = hash_record(path)
        snapshots.append(bound)
    if snapshots[0] != snapshots[1]:
        raise GateFailure("Development package pre/post Body Shop source snapshots differ")
    required_native = {
        "LBBodyShopPrototypeGameMode.cpp",
        "LBBodyShopPrototypeGameMode.h",
        "LBBodyShopPackagedPerformanceBridgeTests.cpp",
    }
    if not required_native.issubset(
        {Path(record["path"]).name for record in snapshots[1].values()}
    ):
        raise GateFailure("Development package does not pin the complete native performance bridge")
    return [snapshots[1][key] for key in sorted(snapshots[1])]


def validate_native_robot_receipt(path: Path) -> dict:
    path = require_file(path, "native six-axis robot fresh-load receipt")
    if sha256(path) != NATIVE_ROBOT_VALIDATION_RECEIPT_SHA256:
        raise GateFailure("native six-axis robot final validation receipt hash drifted")
    lane_summary_path = require_file(path.parent / "lane_summary_v001.json", "native robot lane summary")
    import_receipt_path = require_file(path.parent / "import_receipt_v001.json", "native robot import receipt")
    if (sha256(lane_summary_path) != NATIVE_ROBOT_LANE_SUMMARY_SHA256
            or sha256(import_receipt_path) != NATIVE_ROBOT_IMPORT_RECEIPT_SHA256):
        raise GateFailure("native six-axis robot final import evidence hash drifted")
    lane = json.loads(lane_summary_path.read_text(encoding="utf-8-sig"))
    imported = json.loads(import_receipt_path.read_text(encoding="utf-8-sig"))
    receipt = json.loads(path.read_text(encoding="utf-8-sig"))
    if (lane.get("status")
            != "PASS__INCIDENT_ARCHIVED_NAMESPACE_MOVED_CLEAN_IMPORT_AND_INDEPENDENT_FRESH_LOAD_BODYSHOP_ROBOT_NATIVE_V001"
            or lane.get("import_receipt", {}).get("sha256")
                != NATIVE_ROBOT_IMPORT_RECEIPT_SHA256
            or lane.get("validation_receipt", {}).get("sha256")
                != NATIVE_ROBOT_VALIDATION_RECEIPT_SHA256
            or lane.get("no_ubt_invoked") is not True
            or lane.get("error") is not None
            or imported.get("status")
                != "PASS__INCIDENT_ARCHIVED_AND_INVALID_NAMESPACE_MOVED__FRESH_8_ASSET_3_LOD_HIGH_ELBOW_MONOTONIC_ONE_UV_BODYSHOP_ROBOT_NATIVE_V001_IMPORT"
            or imported.get("baseline_sha256") != NATIVE_ROBOT_BASELINE_SHA256
            or imported.get("clean_disposition_contract_sha256")
                != NATIVE_ROBOT_CLEAN_DISPOSITION_CONTRACT_SHA256):
        raise GateFailure("native six-axis robot final import evidence contract drifted")
    if (
        receipt.get("$schema") != NATIVE_ROBOT_SCHEMA
        or receipt.get("status") != NATIVE_ROBOT_STATUS
        or receipt.get("baseline_sha256") != NATIVE_ROBOT_BASELINE_SHA256
        or receipt.get("clean_disposition_contract_sha256")
            != NATIVE_ROBOT_CLEAN_DISPOSITION_CONTRACT_SHA256
        or receipt.get("import_receipt_sha256")
            != NATIVE_ROBOT_IMPORT_RECEIPT_SHA256
        or receipt.get("destination_namespace") != NATIVE_ROBOT_NAMESPACE
        or receipt.get("asset_count") != 8
        or receipt.get("lod_count_per_asset") != 3
        or receipt.get("source_fbx_count") != 24
        or receipt.get("fresh_process_proof", {}).get("distinct") is not True
        or receipt.get("target_package_hashes_unchanged_by_fresh_load") is not True
        or receipt.get("config_and_existing_promoted_asset_hashes_unchanged") is not True
        or receipt.get("strict_per_asset_triangle_monotonicity") is not True
        or receipt.get("exactly_one_uv_channel_on_all_24_lods") is not True
        or receipt.get("manual_lod_screen_sizes_persisted_after_fresh_process_load") is not True
        or receipt.get("press_v913_map_sha256_unchanged")
            != "26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6"
        or receipt.get("failures")
        or set(receipt.get("assets", {})) != set(EXPECTED_NATIVE_PACKAGES)
    ):
        raise GateFailure("native six-axis robot final validation receipt contract drifted")
    package_rows = []
    triangle_totals = [0, 0, 0]
    for key, expected_package in EXPECTED_NATIVE_PACKAGES.items():
        row = receipt["assets"][key]
        expected_object = expected_package + "." + expected_package.rsplit("/", 1)[-1]
        package_after = row.get("package_after_load", {})
        disk = require_file(
            Path(str(package_after.get("path", ""))),
            f"native six-axis robot {key} package",
        )
        expected_hash = str(package_after.get("sha256", ""))
        if (
            row.get("package_path") != expected_package
            or row.get("object_path") != expected_object
            or row.get("lod_count") != 3
            or not isinstance(row.get("lods"), list)
            or len(row["lods"]) != 3
            or row.get("package_hash_unchanged_by_fresh_load") is not True
            or not re.fullmatch(r"[0-9A-F]{64}", expected_hash)
            or expected_hash != EXPECTED_NATIVE_PACKAGE_HASHES[key]
            or sha256(disk) != expected_hash
        ):
            raise GateFailure(f"native six-axis robot package contract drifted: {key}")
        for lod_index, lod in enumerate(row["lods"]):
            if (lod.get("uv_channels") != 1
                    or not isinstance(lod.get("triangles"), int)):
                raise GateFailure(
                    f"native six-axis robot per-LOD contract drifted: {key}:LOD{lod_index}"
                )
            triangle_totals[lod_index] += lod["triangles"]
        package_rows.append(hash_record(disk))
    if triangle_totals != NATIVE_ROBOT_TRIANGLE_TOTALS:
        raise GateFailure("native six-axis robot aggregate triangle totals drifted")
    return {
        "receipt": hash_record(path),
        "lane_summary": hash_record(lane_summary_path),
        "import_receipt": hash_record(import_receipt_path),
        "baseline_sha256": NATIVE_ROBOT_BASELINE_SHA256,
        "clean_disposition_contract_sha256":
            NATIVE_ROBOT_CLEAN_DISPOSITION_CONTRACT_SHA256,
        "lod_triangle_totals": triangle_totals,
        "packages": package_rows,
    }


def validate_package(package_summary_path: Path, executable_path: Path) -> tuple[dict, dict]:
    package_summary_path = require_file(package_summary_path, "Development package summary")
    package = json.loads(package_summary_path.read_text(encoding="utf-8-sig"))
    if package.get("schema") != PACKAGE_SCHEMA or package.get("status") != PACKAGE_STATUS:
        raise GateFailure(
            f"Development package is not the exact PASS contract: "
            f"schema={package.get('schema')} status={package.get('status')}"
        )
    if (
        package.get("configuration") != "Development"
        or package.get("shipping_requested") is not False
        or package.get("explicit_map") != MAP
        or package.get("protected_unchanged") is not True
    ):
        raise GateFailure("Development package summary contract drifted")
    if (package.get("protected_before", {}).get("press_full_factory_restored_v001")
            != "D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5"
            or package.get("protected_after", {}).get(
                "press_full_factory_restored_v001")
            != "D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5"):
        raise GateFailure("Development package does not protect the full restored Press map")
    if (package.get("protected_before", {}).get("default_game")
            != EXPECTED_DEFAULT_GAME_SHA256
            or package.get("protected_after", {}).get("default_game")
            != EXPECTED_DEFAULT_GAME_SHA256):
        raise GateFailure("Development package does not protect the native cook-root config")

    archive = Path(str(package.get("archive", ""))).resolve()
    if not archive.is_dir():
        raise GateFailure(f"Development package archive is missing: {archive}")
    executable_path = require_file(executable_path, "Packaged Development executable", 4096)
    expected_executable = (
        archive
        / "Windows"
        / "LineBossCarFactory"
        / "Binaries"
        / "Win64"
        / "LineBossCarFactory.exe"
    ).resolve()
    if executable_path != expected_executable or not is_within(executable_path, archive):
        raise GateFailure(
            f"Executable is not the exact archived Development binary: {executable_path}"
        )

    native_robot_receipt = None
    native_support_receipt_path = None
    for key, hash_key, label in (
        ("build_receipt", "build_receipt_sha256", "BuildCookRun receipt"),
        ("manifest_receipt", "manifest_receipt_sha256", "package manifest receipt"),
        (
            "container_listing_receipt",
            "container_listing_receipt_sha256",
            "container listing receipt",
        ),
        (
            "native_robot_fresh_load_validation_receipt",
            "native_robot_fresh_load_validation_receipt_sha256",
            "native six-axis robot fresh-load receipt",
        ),
        (
            "native_support_kit_v002_fresh_load_validation_receipt",
            "native_support_kit_v002_fresh_load_validation_receipt_sha256",
            "native support-kit v002 fresh-load receipt",
        ),
    ):
        evidence = require_file(Path(str(package.get(key, ""))), label)
        if sha256(evidence) != str(package.get(hash_key, "")):
            raise GateFailure(f"{label} hash drifted: {evidence}")
        if key == "native_robot_fresh_load_validation_receipt":
            native_robot_receipt = validate_native_robot_receipt(evidence)
        if key == "native_support_kit_v002_fresh_load_validation_receipt":
            native_support_receipt_path = evidence
    if native_robot_receipt is None:
        raise GateFailure("native six-axis robot fresh-load receipt was not validated")
    project_root = next(
        (parent for parent in native_support_receipt_path.parents
         if (parent / "LineBossCarFactory.uproject").is_file()),
        None,
    )
    if project_root is None or native_support_receipt_path is None:
        raise GateFailure("native support-kit project/receipt authority is missing")
    try:
        native_support_receipt = validate_support_kit(
            project_root, native_support_receipt_path
        )
    except (SupportKitContractError, OSError, json.JSONDecodeError) as exc:
        raise GateFailure("native support-kit v002 authority failed: " + str(exc)) from exc
    manifest_path = require_file(Path(str(package.get("manifest_receipt", ""))),
                                 "package manifest receipt")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    manifest_support = manifest.get("native_support_kit_v002", {})
    if (manifest_support.get("validation_receipt", {}).get("sha256")
            != native_support_receipt["validation_receipt"]["sha256"]
            or manifest_support.get("lod_triangle_totals") != [20408, 7580, 1780]
            or manifest_support.get("asset_count") != 12
            or len(manifest_support.get("packages", {})) != 12):
        raise GateFailure("package manifest does not bind the exact native support-kit v002")
    body_shop_sources = validate_body_shop_source_contract(package)
    return package, {
        "summary": hash_record(package_summary_path),
        "executable": hash_record(executable_path),
        "archive": str(archive),
        "manifest_receipt_sha256": package["manifest_receipt_sha256"],
        "container_listing_receipt_sha256": package["container_listing_receipt_sha256"],
        "native_six_axis_robot": native_robot_receipt,
        "native_support_kit_v002": native_support_receipt,
        "core_renderer_lod_manifest": {
            "component_count": 25,
            "unique_mesh_count": 10,
            "service_props_in_scene_totals_only": True,
        },
        "current_body_shop_sources": body_shop_sources,
    }


def validate_marker(log_path: Path, view_id: str, token: str, receipt_leaf: str) -> dict:
    log_path = require_file(log_path, f"{view_id} packaged engine log")
    text = log_path.read_text(encoding="utf-8-sig", errors="replace")
    if FORBIDDEN_LOG.search(text):
        raise GateFailure(f"{view_id} packaged log contains a fatal/assert/ensure")
    lines = [
        line.strip()
        for line in text.splitlines()
        if "LINE_BOSS_BODY_SHOP_PACKAGED_PERFORMANCE_LOD_V002 view=" in line
    ]
    accepted = []
    for line in lines:
        marker_start = line.find("LINE_BOSS_BODY_SHOP_PACKAGED_PERFORMANCE_LOD_V002 view=")
        marker = line[marker_start:].strip() if marker_start >= 0 else line
        match = EXPECTED_MARKER.fullmatch(marker)
        if match:
            accepted.append((marker, match))
    if len(lines) != 1 or len(accepted) != 1:
        raise GateFailure(
            f"{view_id} log must contain exactly one exact PASS marker; "
            f"found marker_lines={len(lines)} accepted={len(accepted)}"
        )
    marker, match = accepted[0]
    if (
        match.group(1) != view_id.upper()
        or match.group(2) != token
        or match.group(4) != receipt_leaf
        or "null" in match.group(3).lower()
    ):
        raise GateFailure(f"{view_id} marker identity drifted: {marker}")
    return {"marker": marker, "rhi_token": match.group(3), "log": hash_record(log_path)}


def target_contract(runtime: dict, view_id: str) -> tuple[list[dict], dict, dict]:
    summary = runtime.get("target_summary", {})
    targets = runtime.get("target_components")
    snapshot = runtime.get("renderer_lod_snapshot", {})
    configured_time = snapshot.get("view_configured_world_time_seconds")
    snapshot_time = snapshot.get("snapshot_world_time_seconds")
    if (
        summary.get("robot_count") != 3
        or summary.get("component_count") != EXPECTED_COMPONENTS
        or summary.get("unique_mesh_count") != len(EXPECTED_MESHES)
        or summary.get("any_forced_lod") is not False
        or int(summary.get("global_forced_lod", 0)) != -1
        or set(summary.get("unique_mesh_paths", [])) != EXPECTED_MESHES
        or not isinstance(targets, list)
        or len(targets) != EXPECTED_COMPONENTS
    ):
        raise GateFailure(f"{view_id} packaged target summary drifted")
    if (
        not isinstance(snapshot, dict)
        or snapshot.get("thread") != "game_thread"
        or snapshot.get("phase") != "after_120_warmup_frames_before_csv"
        or snapshot.get("selection_source") != "FPrimitiveSceneProxy::GetLOD(FSceneView)"
        or snapshot.get("scene_view_unscaled_size") != [1920, 1080]
        or snapshot.get("component_count") != EXPECTED_COMPONENTS
        or snapshot.get("unique_mesh_count") != len(EXPECTED_MESHES)
        or int(snapshot.get("global_forced_lod", 0)) != -1
        or int(snapshot.get("registered_scene_proxy_component_count", -1))
            < EXPECTED_COMPONENTS
        or snapshot.get("all_targets_rendered_since_view_configured") is not True
        or not isinstance(configured_time, (int, float))
        or not math.isfinite(float(configured_time))
        or float(configured_time) < 0.0
        or not isinstance(snapshot_time, (int, float))
        or not math.isfinite(float(snapshot_time))
        or float(snapshot_time) < float(configured_time)
    ):
        raise GateFailure(f"{view_id} renderer LOD snapshot contract drifted")
    if any(not isinstance(target, dict) for target in targets):
        raise GateFailure(f"{view_id} packaged target array contains a non-object")
    keys = [target.get("key") for target in targets]
    if (any(not isinstance(key, str) or not key for key in keys)
            or len(set(keys)) != EXPECTED_COMPONENTS):
        raise GateFailure(f"{view_id} packaged target keys are not unique")

    canonical = {}
    for target in targets:
        mesh_path = target.get("mesh_path")
        lod_count = int(target.get("lod_count", 0))
        arrays = (
            target.get("lod_screen_sizes"),
            target.get("lod_sections"),
            target.get("lod_triangles"),
            target.get("lod_vertices"),
        )
        selected_lod = int(target.get("selected_lod", -1))
        selected_sections = int(target.get("selected_lod_sections", 0))
        selected_triangles = int(target.get("selected_lod_triangles", 0))
        selected_vertices = int(target.get("selected_lod_vertices", 0))
        last_render_time = target.get("last_render_time_on_screen_seconds")
        last_render_age = target.get("last_render_age_seconds")
        target_snapshot_time = target.get("snapshot_world_time_seconds")
        if (
            mesh_path not in EXPECTED_MESHES
            or target.get("lod_metadata_source")
            != "packaged_runtime_static_mesh_render_data"
            or int(target.get("forced_lod_model", -1)) != 0
            or lod_count < 1
            or not all(isinstance(values, list) and len(values) == lod_count for values in arrays)
            or any(int(value) <= 0 for value in arrays[1] + arrays[2] + arrays[3])
            or selected_lod < 0
            or selected_lod >= lod_count
            or selected_sections != int(arrays[1][selected_lod])
            or selected_triangles != int(arrays[2][selected_lod])
            or selected_vertices != int(arrays[3][selected_lod])
            or target.get("selected_lod_source")
                != "FPrimitiveSceneProxy::GetLOD(FSceneView)"
            or target.get("rendered_since_view_configured") is not True
            or not isinstance(last_render_time, (int, float))
            or not math.isfinite(float(last_render_time))
            or float(last_render_time) < float(configured_time)
            or not isinstance(last_render_age, (int, float))
            or not math.isfinite(float(last_render_age))
            or float(last_render_age) < -0.1
            or float(last_render_age) > 0.5
            or not isinstance(target_snapshot_time, (int, float))
            or not math.isfinite(float(target_snapshot_time))
            or float(target_snapshot_time) != float(snapshot_time)
            or abs(
                float(target_snapshot_time)
                - float(last_render_time)
                - float(last_render_age)
            ) > 0.001
            or not target.get("actor_full_name")
            or not target.get("component_name")
        ):
            raise GateFailure(f"{view_id} packaged target LOD metadata drifted: {target.get('key')}")
        canonical[target["key"]] = {
            key: target.get(key)
            for key in (
                "category",
                "identity",
                "component_name",
                "mesh_path",
                "lod_count",
                "lod_screen_sizes",
                "lod_sections",
                "lod_triangles",
                "lod_vertices",
                "forced_lod_model",
            )
        }
    return targets, canonical, snapshot


def renderer_lod_selection(targets: list[dict], view_id: str) -> dict:
    rows = []
    by_mesh = {}
    total_sections = 0
    total_triangles = 0
    total_vertices = 0
    for target in targets:
        selected_lod = int(target["selected_lod"])
        sections = int(target["selected_lod_sections"])
        triangles = int(target["selected_lod_triangles"])
        vertices = int(target["selected_lod_vertices"])
        row = {
            "key": target["key"],
            "category": target["category"],
            "actor": target["actor_full_name"],
            "component": target["component_name"],
            "mesh_path": target["mesh_path"],
            "available_lods": target["lod_count"],
            "screen_sizes": target["lod_screen_sizes"],
            "automatic_lod": True,
            "renderer_selected_lod": selected_lod,
            "selected_lod_sections": sections,
            "selected_lod_triangles": triangles,
            "selected_lod_vertices": vertices,
            "selection_source": target["selected_lod_source"],
            "last_render_time_on_screen_seconds":
                float(target["last_render_time_on_screen_seconds"]),
        }
        rows.append(row)
        by_mesh.setdefault(target["mesh_path"], []).append({
            "target": target["key"],
            "lod": selected_lod,
            "sections": sections,
            "triangles": triangles,
            "vertices": vertices,
        })
        total_sections += sections
        total_triangles += triangles
        total_vertices += vertices
    if len(rows) != EXPECTED_COMPONENTS:
        raise GateFailure(f"{view_id} renderer LOD selection is incomplete")
    return {
        "selection_source": "FPrimitiveSceneProxy::GetLOD(FSceneView)",
        "target_component_lods": rows,
        "target_lod_totals": {
            "components": len(rows),
            "sections": total_sections,
            "triangles": total_triangles,
            "vertices": total_vertices,
        },
        "selected_lods_by_mesh": [
            {"mesh_path": mesh, "instances": instances}
            for mesh, instances in sorted(by_mesh.items())
        ],
    }


def runtime_view(
    receipt_path: Path, log_path: Path, expected_view: str, run_root: Path
) -> tuple[dict, dict, dict]:
    receipt_path = require_file(receipt_path, f"{expected_view} runtime receipt")
    log_path = require_file(log_path, f"{expected_view} engine log")
    if not is_within(receipt_path, run_root) or not is_within(log_path, run_root):
        raise GateFailure(f"{expected_view} receipt/log escapes the packaged performance run root")
    runtime = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
    if (
        runtime.get("$schema") != RUNTIME_SCHEMA
        or runtime.get("status") != RUNTIME_STATUS
        or runtime.get("view") != expected_view
        or runtime.get("map") != MAP
    ):
        raise GateFailure(f"{expected_view} runtime receipt identity drifted")
    token = str(runtime.get("token", ""))
    if not re.fullmatch(r"[A-Za-z0-9_-]{16,96}", token):
        raise GateFailure(f"{expected_view} runtime token is unsafe")

    contract = runtime.get("capture_contract", {})
    rhi = runtime.get("rhi", {})
    if (
        contract.get("surface") != "packaged_development_game"
        or contract.get("viewport") != [1920, 1080]
        or contract.get("warmup_frames") != 120
        or contract.get("csv_capture_frames") != 300
        or contract.get("force_res") is not True
        or contract.get("real_rhi_required") is not True
        or contract.get("null_rhi_forbidden") is not True
        or contract.get("gpu_csv_stats_required") is not True
        or contract.get("renderer_lod_snapshot_phase")
            != "game_thread_after_warmup_before_csv"
        or contract.get("renderer_lod_selection_source")
            != "FPrimitiveSceneProxy::GetLOD(FSceneView)"
        or contract.get("primitive_debug_dump_used") is not False
        or contract.get("visible_primitives_budget_authority")
            != "registered_scene_proxy_component_upper_bound"
        or rhi.get("can_ever_render") is not True
        or rhi.get("null_rhi_command_line") is not False
        or int(rhi.get("r.GPUCsvStatsEnabled", -1)) != 1
        or not str(rhi.get("graphics_rhi", ""))
        or "null" in str(rhi.get("graphics_rhi", "")).lower()
    ):
        raise GateFailure(f"{expected_view} is not exact 1920x1080 real-RHI packaged evidence")

    if "primitive_csv_candidates" in runtime:
        raise GateFailure(f"{expected_view} stale primitive-dump evidence is forbidden")
    targets, canonical, lod_snapshot = target_contract(runtime, expected_view)
    marker = validate_marker(log_path, expected_view, token, receipt_path.name)
    profile_record = runtime.get("raw_csv", {})
    profile = require_file(Path(str(profile_record.get("path", ""))), f"{expected_view} CSV", 4096)
    if (
        not is_within(profile, run_root)
        or profile.stat().st_size != int(profile_record.get("bytes", -1))
        or int(profile_record.get("requested_frames", -1)) != 300
    ):
        raise GateFailure(f"{expected_view} CSV path/length/frame contract drifted")

    profile_bound = hash_record(profile)
    profile_metrics, _headers = legacy.profile_metrics(profile)
    if profile_metrics["captured_frames"] != 300:
        raise GateFailure(
            f"{expected_view} CSV contains {profile_metrics['captured_frames']} frames, expected exactly 300"
        )
    lod_selection = renderer_lod_selection(targets, expected_view)
    camera = runtime.get("camera", {})
    if camera.get("viewport") != [1920, 1080]:
        raise GateFailure(f"{expected_view} camera viewport drifted")
    evidence = {
        "runtime_receipt": hash_record(receipt_path),
        "engine_log_and_marker": marker,
        "raw_csv": profile_bound,
        "camera": camera,
        "rhi": rhi,
        "target_summary": runtime["target_summary"],
        "performance": profile_metrics,
        "renderer_lod_snapshot": lod_snapshot,
        "renderer_lod_selection": lod_selection,
    }
    return runtime, canonical, evidence


def analyse(
    package_summary: Path,
    executable: Path,
    management_receipt: Path,
    focus_receipt: Path,
    management_log: Path,
    focus_log: Path,
    run_root: Path,
    output: Path,
) -> dict:
    payload = {
        "$schema": "cairnwell/body-shop/experimental-v001/packaged-performance-lod-gate/v2",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "IN_PROGRESS",
        "budgets": PACKAGED_BUDGETS,
        "package": {},
        "views": {},
        "checks": {},
        "failures": [],
    }
    try:
        run_root = run_root.resolve()
        if not run_root.is_dir() or not is_within(output, run_root):
            raise GateFailure("Analyzer output/run-root contract is invalid")
        _package, package_evidence = validate_package(package_summary, executable)
        payload["package"] = package_evidence

        management, management_canonical, management_evidence = runtime_view(
            management_receipt, management_log, "management", run_root
        )
        focus, focus_canonical, focus_evidence = runtime_view(
            focus_receipt, focus_log, "focus", run_root
        )
        if management["token"] != focus["token"]:
            raise GateFailure("Management/focus receipts do not share one exact run token")
        if management_canonical != focus_canonical:
            raise GateFailure("Management/focus runtime target LOD metadata differs")

        for view_id, evidence in (
            ("management", management_evidence),
            ("focus", focus_evidence),
        ):
            metrics = evidence["performance"]["metrics"]
            scene_budget_measurements = {
                "visible_primitives": int(
                    evidence["renderer_lod_snapshot"][
                        "registered_scene_proxy_component_count"
                    ]
                ),
                "draw_calls": metrics["rhi_draw_calls"]["p95"],
                "triangles": metrics["rhi_primitives_drawn"]["p95"],
            }
            evidence["scene_budget_measurements"] = scene_budget_measurements
            evidence["scene_budget_measurement_sources"] = {
                "visible_primitives":
                    "conservative_registered_scene_proxy_component_upper_bound",
                "draw_calls": "300_frame_csv_rhi_draw_calls_p95",
                "triangles": "300_frame_csv_rhi_primitives_drawn_p95",
            }
            budget_checks = legacy.evaluate_budgets(
                view_id,
                evidence["performance"],
                {"scene_totals": scene_budget_measurements},
                payload["failures"],
            )
            evidence["budget_checks"] = budget_checks
            payload["views"][view_id] = evidence

        management_zoom = float(management_evidence["camera"].get("zoom_distance_cm", 0.0))
        focus_zoom = float(focus_evidence["camera"].get("zoom_distance_cm", 0.0))
        distinct = management_zoom >= focus_zoom + 1500.0
        payload["checks"]["representative_management_and_focus_cameras"] = {
            "passed": distinct,
            "management_zoom_distance_cm": management_zoom,
            "focus_zoom_distance_cm": focus_zoom,
            "viewport": [1920, 1080],
        }
        if not distinct:
            payload["failures"].append(
                "Management/focus packaged cameras are not distinct representative views"
            )

        for view_id, evidence in payload["views"].items():
            lod_rows = evidence["renderer_lod_selection"]["target_component_lods"]
            passed = (
                len(lod_rows) == EXPECTED_COMPONENTS
                and len({row["mesh_path"] for row in lod_rows}) == len(EXPECTED_MESHES)
                and all(row["renderer_selected_lod"] >= 0 for row in lod_rows)
            )
            payload["checks"][f"{view_id}_all_target_lods_proven"] = {
                "passed": passed,
                "component_count": len(lod_rows),
                "unique_mesh_count": len({row["mesh_path"] for row in lod_rows}),
            }
            if not passed:
                payload["failures"].append(f"{view_id} renderer-selected LOD proof is incomplete")
        payload["status"] = PASS_STATUS if not payload["failures"] else FAIL_STATUS
    except Exception as exc:
        payload["failures"].append(str(exc))
        payload["status"] = FAIL_STATUS
    payload["finished_utc"] = datetime.now(timezone.utc).isoformat()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-summary", required=True, type=Path)
    parser.add_argument("--executable", required=True, type=Path)
    parser.add_argument("--management-receipt", required=True, type=Path)
    parser.add_argument("--focus-receipt", required=True, type=Path)
    parser.add_argument("--management-log", required=True, type=Path)
    parser.add_argument("--focus-log", required=True, type=Path)
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    result = analyse(
        args.package_summary.resolve(),
        args.executable.resolve(),
        args.management_receipt.resolve(),
        args.focus_receipt.resolve(),
        args.management_log.resolve(),
        args.focus_log.resolve(),
        args.run_root.resolve(),
        args.output.resolve(),
    )
    print(result["status"])
    for failure in result["failures"]:
        print("FAIL:", failure)
    return 0 if result["status"] == PASS_STATUS else 2


if __name__ == "__main__":
    sys.exit(main())
