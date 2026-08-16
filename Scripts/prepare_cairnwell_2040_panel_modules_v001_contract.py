"""Freeze clean source-authority v002 into the stable v001 Unreal panel lane.

Offline standard Python only.  This tool cannot launch Unreal.  It writes only
the new panel-lane contract and sidecar, refuses overwrite, and remains unusable
until both of these independent authorities exist and pass their exact gates:

* the visually/geometry-approved parametric-authored v002 11-panel freeze; and
* the exact incident-bound Cairnwell2040Runtime_v001 recovery import/fresh-load PASS.

The panel lane imports meshes only.  It references the already persisted
galvanised, ED-coat, and player-paint materials from the approved vehicle
runtime and never duplicates its textures or materials.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8").resolve()
OUTPUT = PROJECT / "Scripts/cairnwell_2040_panel_modules_v001_import_contract.json"
OUTPUT_SHA = PROJECT / "Scripts/cairnwell_2040_panel_modules_v001_import_contract.sha256"
SOURCE_ROOT = PROJECT / (
    "SourceAssets/Candidate/Vehicles/Cairnwell2040/"
    "Cairnwell2040PanelModules_v002"
)
SOURCE_MANIFEST = SOURCE_ROOT / "MANIFEST_Cairnwell2040PanelModules_v002.json"
SOURCE_PRODUCTION_AUDIT = (
    SOURCE_ROOT / "Audit/Cairnwell2040PanelModules_v002_ProductionAudit.json"
)
SOURCE_FREEZE_RECEIPT = (
    SOURCE_ROOT / "Audit/Cairnwell2040PanelModules_v002_FreezeReceipt.json"
)
EXPECTED_SOURCE_MANIFEST_SHA256 = (
    "2FF38357BEC9FB890B2DCCCBC4C5E1728AB35D5BCB772F08811522540F6DF6E8"
)
EXPECTED_SOURCE_PRODUCTION_AUDIT_SHA256 = (
    "F7C9CF062DBC1E5A4B5CBFE8B71A9BD79E1536D0523802F8F118562E9CC24762"
)
EXPECTED_SOURCE_FREEZE_RECEIPT_SHA256 = (
    "B31900FE90D237952E788361309B747B8C7D831536034CBD23894408E0925B3D"
)
EXPECTED_V005_MANIFEST_SHA256 = (
    "FADE2251A090D36351317C5F9FB9758586B8F7E2A65B25CA54325B289D3A72B7"
)
V005_MANIFEST = PROJECT / (
    "SourceAssets/Candidate/Vehicles/Cairnwell2040/"
    "FinishedVehicleRuntimeDerivative_v001/ProductionCandidate_v005/MANIFEST_v005.json"
)
DEST = (
    "/Game/LineBoss/Factory/OneFactory/v001/Vehicles/"
    "Cairnwell2040PanelModules_v001"
)
DEST_DISK = PROJECT / (
    "Content/LineBoss/Factory/OneFactory/v001/Vehicles/"
    "Cairnwell2040PanelModules_v001"
)
AUDIT_ROOT = PROJECT / (
    "Saved/Audits/OneFactory/Vehicles/Cairnwell2040PanelModules_v001/"
    "UnrealImportLane_v001"
)
RUNTIME_DEST = (
    "/Game/LineBoss/Factory/OneFactory/v001/Vehicles/"
    "Cairnwell2040Runtime_v001"
)
RUNTIME_CONTRACT = PROJECT / "Scripts/cairnwell_2040_runtime_v001_import_contract.json"
RUNTIME_CONTRACT_SHA = PROJECT / "Scripts/cairnwell_2040_runtime_v001_import_contract.sha256"
RUNTIME_BASELINE = PROJECT / "Scripts/cairnwell_2040_runtime_v001_import_baseline.json"
RUNTIME_BASELINE_SHA = PROJECT / "Scripts/cairnwell_2040_runtime_v001_import_baseline.sha256"
RUNTIME_RECOVERY_V013_CONTRACT = (
    PROJECT / "Scripts/cairnwell_2040_runtime_v001_recovery_v013_contract.json"
)
RUNTIME_RECOVERY_V013_CONTRACT_SHA = (
    PROJECT / "Scripts/cairnwell_2040_runtime_v001_recovery_v013_contract.sha256"
)
RUNTIME_AUDIT_ROOT = PROJECT / (
    "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
    "UnrealImportLane_v001"
)
RUNTIME_RECOVERY_V013_AUDIT_ROOT = RUNTIME_AUDIT_ROOT / "Recovery_v013"
RUNTIME_RECOVERY_V013_RUN_ID = "20260815T172802Z-1389784f"
RUNTIME_RECOVERY_V013_RUN_ROOT = (
    RUNTIME_RECOVERY_V013_AUDIT_ROOT / RUNTIME_RECOVERY_V013_RUN_ID
)
ACK_TOKEN = "FREEZE_APPROVED_CAIRNWELL_2040_PANEL_MODULES_V001_CONTRACT"
SOURCE_AUTHORITY_VERSION = "v002"
UNREAL_DESTINATION_VERSION = "v001"
PANEL_SCHEMA = "lineboss.cairnwell2040.panel-modules.v002"
PANEL_STATUS = "APPROVED__PARAMETRIC_AUTHORED_CLEAN_SHARED_DATUM_PANEL_MODULES_V002"
CONTRACT_STATUS = "FROZEN__APPROVED_CAIRNWELL_2040_PANEL_MODULES_V001__READY_FOR_BASELINE"
RUNTIME_CONTRACT_SCHEMA = "lineboss/cairnwell-2040-runtime-v001/unreal-import-contract/v1"
RUNTIME_CONTRACT_STATUS = "FROZEN__APPROVED_CAIRNWELL_V005_WINNER__READY_FOR_BASELINE"
RUNTIME_BASELINE_SCHEMA = "lineboss/cairnwell-2040-runtime-v001/unreal-import-baseline/v1"
RUNTIME_BASELINE_STATUS = "FROZEN__CAIRNWELL_2040_RUNTIME_V001_PROJECT_BASELINE"
EXPECTED_RUNTIME_CONTRACT_SHA256 = (
    "B0D276A85E8532B580098092384BD93D0E5F55E3A437922FFFC31D69B8816EB1"
)
EXPECTED_RUNTIME_BASELINE_SHA256 = (
    "493CEBCA0DAA09179D0F44BE2FE4E4D60658D8F42CD88A02268045591EE77882"
)
RUNTIME_RECOVERY_V013_SCHEMA = (
    "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v13"
)
RUNTIME_RECOVERY_V013_STATUS = (
    "FROZEN__CAIRNWELL_2040_RUNTIME_V001_INCIDENT_CHAINED_RECOVERY_V013__"
    "READY_FOR_ONE_SHOT_VALIDATION_ONLY_OF_V009_PASS_IMPORT"
)
EXPECTED_RUNTIME_RECOVERY_V013_CONTRACT_SHA256 = (
    "5D2B1929086AD33A8354ED0759509BCC6AFFEF8CD4E5BDE77A54546B53E95F12"
)
EXPECTED_RUNTIME_INCIDENT_CHAIN_SHA256 = (
    "392E5F5D4B3291D69F770B797982BD34D06992A45A78EB5F36CE3C66C257D874"
)
RUNTIME_V013_VALIDATION_SCHEMA = (
    "lineboss/audit/cairnwell-2040-runtime-v001/recovery-v013/"
    "fresh-process-validation/v13"
)
RUNTIME_V013_VALIDATION_STATUS = (
    "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V013_DISTINCT_FRESH_PROCESS__"
    "READ_ONLY_RELOAD_OF_V009_PASS_IMPORT__EXACT_PERSISTED_DEPENDENCIES__"
    "ZERO_CACHE_DELETION_OR_WRITE__11_PACKAGE_HASHES_UNCHANGED"
)
RUNTIME_V013_SUMMARY_SCHEMA = (
    "lineboss/audit/cairnwell-2040-runtime-v001/recovery-v013/"
    "validation-only-lane-summary/v13"
)
RUNTIME_V013_SUMMARY_STATUS = (
    "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V013_GUARDED_"
    "VALIDATION_ONLY_OF_V009_PASS_IMPORT"
)
RUNTIME_V013_RESULT_FILES = {
    "fresh_process_validation_receipt_recovery_v013.json": (
        63160, "54A332C47FE71CE975EE666331882369855770C13B81CE6C195488A957127E44"
    ),
    "fresh_process_validation_recovery_v013.log": (
        402734, "75D0C27913C1F9F384BAF0E51FC7DDEC048B5F5C6184348D70F93829A5D3E32C"
    ),
    "fresh_process_validation_recovery_v013.stderr.log": (
        0, "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"
    ),
    "fresh_process_validation_recovery_v013.stdout.log": (
        404081, "238F34F429471415B746C0AB381A497E6F2B2E883E9188A5AFB5329EBB2C5B7E"
    ),
    "lane_summary_recovery_v013.json": (
        8640, "D24261F1929D3B44EBF6526C148E044A403006DB738F52257A1A16D9CB432488"
    ),
}

PANEL_IDS = (
    "HOOD_PANEL",
    "ROOF_PANEL",
    "DOOR_FRONT_LEFT",
    "DOOR_FRONT_RIGHT",
    "DOOR_REAR_LEFT",
    "DOOR_REAR_RIGHT",
    "FENDER_FRONT_LEFT",
    "FENDER_FRONT_RIGHT",
    "QUARTER_PANEL_LEFT",
    "QUARTER_PANEL_RIGHT",
    "TAILGATE_PANEL",
)
EXPECTED_ASSET_NAMES = {
    panel_id: f"SM_LB_C2040_{panel_id}_v001" for panel_id in PANEL_IDS
}
EXPECTED_SOURCE_ASSET_NAMES = {
    panel_id: f"SM_LB_C2040_{panel_id}_v002" for panel_id in PANEL_IDS
}
SEMANTIC_SLOT = "VehiclePanelSurface"
RUNTIME_MATERIALS = {
    "biw_galvanised": (
        "M_LB_C2040_BIWGalvanized_v001",
        "Materials/M_LB_C2040_BIWGalvanized_v001",
    ),
    "ed_coat": (
        "M_LB_C2040_EDCoat_v001",
        "Materials/M_LB_C2040_EDCoat_v001",
    ),
    "player_paint": (
        "M_LB_C2040_BodyPaintTintPBR_v001",
        "Materials/M_LB_C2040_BodyPaintTintPBR_v001",
    ),
}
DEFAULT_MATERIAL_ROLE = "player_paint"
CAR_DIMENSIONS_CM = [456.0, 188.0, 156.0]
CAR_ENVELOPE_MIN_CM = [-228.0, -94.0, 0.0]
CAR_ENVELOPE_MAX_CM = [228.0, 94.0, 156.0]
BOUNDS_TOLERANCE_CM = 0.25
ROUNDTRIP_BOUNDS_TOLERANCE_CM = 0.001
MAPLESS_STARTUP_OVERRIDE = (
    "-ini:EditorPerProjectUserSettings:"
    "[/Script/UnrealEd.EditorLoadingSavingSettings]:LoadLevelAtStartup=None"
)
RESULT_NAMES = {
    "import_receipt_v001.json",
    "import_failure_v001.json",
    "fresh_process_validation_receipt_v001.json",
    "fresh_process_validation_failure_v001.json",
    "lane_summary_v001.json",
}


class ContractError(RuntimeError):
    """Fail-closed contract preparation error."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT).as_posix()
    except ValueError as exc:
        raise ContractError(f"authority path escapes exact project: {path}") from exc


def row(path: Path, expected: dict | None = None) -> dict:
    if not path.is_file():
        raise ContractError(f"required authority file is absent: {path}")
    actual = {"path": relative(path), "bytes": path.stat().st_size, "sha256": sha256(path)}
    if expected is not None:
        if not isinstance(expected, dict):
            raise ContractError(f"authority row must be an object: {path}")
        if any(actual[key] != expected.get(key) for key in ("path", "bytes", "sha256")):
            raise ContractError(f"authority hash/size/path drift: {path}")
    return actual


def strict_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"duplicate raw JSON property forbidden: {key!r}")
        result[key] = value
    return result


def strict_json_file(path: Path, label: str) -> dict:
    try:
        data = json.loads(
            path.read_text(encoding="utf-8-sig"), object_pairs_hook=strict_pairs
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"{label} JSON is unreadable") from exc
    if not isinstance(data, dict):
        raise ContractError(f"{label} must be a JSON object")
    return data


def sidecar(payload: Path, digest_path: Path, label: str) -> tuple[dict, str]:
    if not payload.is_file() or not digest_path.is_file():
        raise ContractError(f"{label} payload or SHA-256 sidecar is absent")
    digest = sha256(payload)
    expected = digest_path.read_text(encoding="ascii").strip().split()[0].upper()
    if expected != digest:
        raise ContractError(f"{label} SHA-256 sidecar drift")
    data = strict_json_file(payload, label)
    return data, digest


def vector(value, field: str) -> list[float]:
    if not isinstance(value, list) or len(value) != 3:
        raise ContractError(f"{field} must contain exactly three coordinates")
    answer = [round(float(component), 6) for component in value]
    if any(not math.isfinite(component) for component in answer):
        raise ContractError(f"{field} contains a non-finite coordinate")
    return answer


def json_object(path: Path, label: str) -> dict:
    return strict_json_file(path, label)


def exact_sha_row(path: Path, expected_sha256: str, label: str) -> dict:
    actual = row(path)
    if actual["sha256"] != expected_sha256:
        raise ContractError(f"{label} exact frozen SHA-256 drift")
    return actual


def source_freeze_authority(manifest: dict) -> dict:
    """Verify the exact approved v002 tree, audit, receipt, and frozen inventory."""
    manifest_row = exact_sha_row(
        SOURCE_MANIFEST, EXPECTED_SOURCE_MANIFEST_SHA256, "panel source manifest"
    )
    audit_row = exact_sha_row(
        SOURCE_PRODUCTION_AUDIT,
        EXPECTED_SOURCE_PRODUCTION_AUDIT_SHA256,
        "panel production audit",
    )
    receipt_row = exact_sha_row(
        SOURCE_FREEZE_RECEIPT,
        EXPECTED_SOURCE_FREEZE_RECEIPT_SHA256,
        "panel source freeze receipt",
    )
    if json_object(SOURCE_MANIFEST, "panel source manifest") != manifest:
        raise ContractError("provided manifest object differs from the exact frozen source file")
    audit = json_object(SOURCE_PRODUCTION_AUDIT, "panel production audit")
    receipt = json_object(SOURCE_FREEZE_RECEIPT, "panel source freeze receipt")
    if (
        receipt.get("$schema")
        != "lineboss.cairnwell2040.panel-modules.freeze-receipt.v002"
        or receipt.get("status")
        != "FROZEN__SOURCEASSETS_ONLY__NO_UNREAL_IMPORT_OR_PROMOTION"
        or receipt.get("selected_version") != SOURCE_AUTHORITY_VERSION
        or receipt.get("manifest") != manifest_row
        or receipt.get("production_audit") != audit_row
        or int(receipt.get("file_count_before_receipt", -1)) != 109
        or receipt.get("protected_v005_byte_exact") is not True
        or receipt.get("rejected_v001_or_preview_outputs_modified") is not False
    ):
        raise ContractError("panel source freeze receipt identity/safety gate drift")
    inventory = receipt.get("inventory_before_receipt")
    if not isinstance(inventory, list) or len(inventory) != 109:
        raise ContractError("panel source freeze inventory must contain exactly 109 pre-receipt files")
    frozen_rows = {}
    for expected in inventory:
        if not isinstance(expected, dict):
            raise ContractError("panel source freeze inventory row is not an object")
        path = (PROJECT / str(expected.get("path", ""))).resolve()
        try:
            path.relative_to(SOURCE_ROOT.resolve())
        except ValueError as exc:
            raise ContractError("panel source freeze inventory escapes the v002 root") from exc
        actual = row(path, expected)
        if actual["path"] in frozen_rows:
            raise ContractError("panel source freeze inventory contains a duplicate path")
        frozen_rows[actual["path"]] = actual
    receipt_relative = relative(SOURCE_FREEZE_RECEIPT)
    if receipt_relative in frozen_rows:
        raise ContractError("freeze receipt incorrectly appears in its pre-receipt inventory")
    actual_tree = {
        relative(path)
        for path in SOURCE_ROOT.rglob("*")
        if path.is_file()
    }
    if actual_tree != set(frozen_rows) | {receipt_relative}:
        raise ContractError("approved v002 source tree acquired missing or unpinned files")
    if (
        audit.get("$schema")
        != "lineboss.cairnwell2040.panel-modules.production-audit.v002"
        or audit.get("status") != "PASS"
        or audit.get("manifest") != manifest_row
        or int(audit.get("panel_count", -1)) != 11
        or tuple(audit.get("panel_roles", [])) != PANEL_IDS
    ):
        raise ContractError("panel production audit identity/count/order drift")
    return {
        "manifest": manifest_row,
        "production_audit": audit_row,
        "freeze_receipt": receipt_row,
        "production_audit_payload": audit,
        "frozen_inventory_before_receipt": [
            frozen_rows[key] for key in sorted(frozen_rows, key=str.casefold)
        ],
        "frozen_file_count_including_receipt": 110,
    }


def empty_key_paths(value, prefix=()):
    """Return raw object paths that contain an empty-string key."""
    found = []
    if isinstance(value, dict):
        if "" in value:
            found.append(".".join(prefix))
        for key, child in value.items():
            found.extend(empty_key_paths(child, prefix + (str(key),)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(empty_key_paths(child, prefix + (str(index),)))
    return found


def runtime_v013_pass(recovery_digest: str) -> dict:
    """Accept only the exact consumed V013 five-file PASS; never discover latest PASS."""
    root = RUNTIME_RECOVERY_V013_RUN_ROOT.resolve()
    parent = RUNTIME_RECOVERY_V013_AUDIT_ROOT.resolve()
    if not parent.is_dir():
        raise ContractError("exact runtime Recovery_v013 authority root is absent")
    direct_files = [path for path in parent.iterdir() if path.is_file()]
    run_roots = [path.resolve() for path in parent.iterdir() if path.is_dir()]
    if direct_files or run_roots != [root]:
        raise ContractError("runtime V013 authority must contain only its exact pinned run")
    if not root.is_dir() or any(path.is_dir() for path in root.iterdir()):
        raise ContractError("exact runtime V013 run is absent or has nested directories")
    actual_names = {path.name for path in root.iterdir() if path.is_file()}
    if actual_names != set(RUNTIME_V013_RESULT_FILES):
        raise ContractError("runtime V013 result must remain the exact five-file closure")

    evidence = {}
    for filename, (expected_bytes, expected_digest) in RUNTIME_V013_RESULT_FILES.items():
        checked = row(root / filename)
        if checked["bytes"] != expected_bytes or checked["sha256"] != expected_digest:
            raise ContractError(f"runtime V013 exact result drift: {filename}")
        evidence[filename] = checked

    receipt_path = root / "fresh_process_validation_receipt_recovery_v013.json"
    summary_path = root / "lane_summary_recovery_v013.json"
    receipt = strict_json_file(receipt_path, "runtime V013 validation receipt")
    summary = strict_json_file(summary_path, "runtime V013 lane summary")
    packages = receipt.get("package_sha256_before_loads")
    cache = receipt.get("asset_registry_cache_before")
    legacy = receipt.get("legacy_asset_registry_cache_absence_before")
    source = {"file_count": 26, "inventory_sha256":
              "C5D7F19A1886EF6E9FAA80F0118343AEAF2DD773B9E8B8DB5EAA4025068A9C58"}
    protected = {"file_count": 15670, "inventory_sha256":
                 "EBBCE409A82768D6C0AE90F78C55656022D97B8A3A87E78D132A144A6B2E5559"}
    prepared_lane = {"file_count": 69, "inventory_sha256":
                     "0F6D5AC2817C3038234A22B436DF5C7A4F0080D2FFB1443987FBAC3D4D792047"}
    if (
        receipt.get("$schema") != RUNTIME_V013_VALIDATION_SCHEMA
        or receipt.get("status") != RUNTIME_V013_VALIDATION_STATUS
        or summary.get("$schema") != RUNTIME_V013_SUMMARY_SCHEMA
        or summary.get("status") != RUNTIME_V013_SUMMARY_STATUS
        or receipt.get("recovery_contract_sha256") != recovery_digest
        or summary.get("recovery_contract_sha256") != recovery_digest
        or receipt.get("contract_sha256") != EXPECTED_RUNTIME_CONTRACT_SHA256
        or receipt.get("baseline_sha256") != EXPECTED_RUNTIME_BASELINE_SHA256
        or summary.get("contract_sha256") != EXPECTED_RUNTIME_CONTRACT_SHA256
        or summary.get("baseline_sha256") != EXPECTED_RUNTIME_BASELINE_SHA256
        or receipt.get("incident_chain_sha256")
        != EXPECTED_RUNTIME_INCIDENT_CHAIN_SHA256
        or Path(str(summary.get("run_root", ""))).resolve() != root
    ):
        raise ContractError("runtime V013 schema/status/run/authority binding drift")
    if (
        not isinstance(packages, dict)
        or len(packages) != 11
        or receipt.get("package_sha256_after_loads") != packages
        or summary.get("post_exit_package_sha256") != packages
        or receipt.get("all_package_hashes_unchanged") is not True
        or receipt.get("persisted_asset_registry_dependency_closure_verified") is not True
        or type(receipt.get("package_count")) is not int
        or receipt["package_count"] != 11
        or type(receipt.get("asset_mutation_count")) is not int
        or receipt["asset_mutation_count"] != 0
        or receipt.get("asset_mutations") != []
        or type(receipt.get("asset_registry_cache_mutation_count")) is not int
        or receipt["asset_registry_cache_mutation_count"] != 0
        or type(receipt.get("legacy_asset_registry_cache_mutation_count")) is not int
        or receipt["legacy_asset_registry_cache_mutation_count"] != 0
        or type(receipt.get("import_or_reimport_process_count")) is not int
        or receipt["import_or_reimport_process_count"] != 0
        or receipt.get("project_maps_loaded_or_saved") != []
    ):
        raise ContractError("runtime V013 exact 11-package/read-only closure drift")
    process_id = receipt.get("process_id")
    import_process_id = receipt.get("import_process_id")
    if (
        type(process_id) is not int
        or type(import_process_id) is not int
        or process_id <= 0
        or import_process_id <= 0
        or process_id == import_process_id
        or receipt.get("validator_process_id") != process_id
        or receipt.get("distinct_process_verified") is not True
        or summary.get("validation_process", {}).get("process_id") != process_id
        or summary.get("validation_process", {}).get("exit_code") != 0
        or summary.get("validation_process", {}).get(
            "fatal_or_build_tool_log_patterns") != []
        or summary.get("editor_process_count") != 1
        or summary.get("import_process_count") != 0
        or summary.get("content_move_count") != 0
        or summary.get("no_build_tool_invoked") is not True
        or summary.get("exact_ubt_command_line_matches") != 0
        or summary.get("environment_restoration_verified") is not True
        or summary.get("strict_exit_zero_no_fatal_and_no_ubt_log_required") is not True
        or summary.get("error") is not None
    ):
        raise ContractError("runtime V013 distinct-process/natural-exit/zero-UBT evidence drift")
    if (
        receipt.get("source_before") != source
        or receipt.get("source_after") != source
        or receipt.get("protected_before") != protected
        or receipt.get("protected_after") != protected
        or receipt.get("prepared_lane_before") != prepared_lane
        or receipt.get("prepared_lane_after") != prepared_lane
        or not isinstance(cache, dict)
        or cache.get("file_count") != 2
        or cache.get("inventory_sha256")
        != "59DEFE0409EA024EA6FF7B4CF2B7FEF7CD8FC8D652EE356D76ACE7DC2767B3E9"
        or receipt.get("asset_registry_cache_after") != cache
        or summary.get("post_exit_asset_registry_cache") != cache
        or not isinstance(legacy, dict)
        or legacy.get("matching_path_count") != 0
        or legacy.get("monolithic_absent") is not True
        or legacy.get("legacy_shard_paths") != []
        or receipt.get("legacy_asset_registry_cache_absence_after") != legacy
        or summary.get("post_exit_legacy_asset_registry_cache_absence") != legacy
        or receipt.get("no_asset_registry_cache_write_command_line_verified") is not True
        or receipt.get("ubt_startup_guard_environment")
        != {"name": "UE_SKIP_UBT_SDK_SETUP", "observed_value": "1",
            "required_value": "1"}
    ):
        raise ContractError("runtime V013 source/protected/lane/cache invariance drift")
    if empty_key_paths(receipt) != [
        "assets.materials.body.graph.detail_clamp.inputs"
    ]:
        raise ContractError("runtime V013 strict sole empty material-input key path drift")
    model = (
        receipt.get("vehicle_model_id"),
        receipt.get("production_recipe_id"),
        receipt.get("current_geometry_authority_id"),
    )
    if model != (
        "CAIRNWELL_2040",
        "CAIRNWELL_2040_DEVELOPMENT_RECIPE_V001",
        "Cairnwell2040Runtime_v001_V009ImportedGeometry",
    ) or model != (
        summary.get("vehicle_model_id"),
        summary.get("production_recipe_id"),
        summary.get("current_geometry_authority_id"),
    ):
        raise ContractError("runtime V013 stable DEVELOPMENT model identity drift")
    validation_row = summary.get("validation_receipt", {})
    if (
        validation_row.get("sha256")
        != RUNTIME_V013_RESULT_FILES[
            "fresh_process_validation_receipt_recovery_v013.json"][1]
        or validation_row.get("status") != RUNTIME_V013_VALIDATION_STATUS
        or summary.get("validation_process", {}).get("log_sha256")
        != RUNTIME_V013_RESULT_FILES[
            "fresh_process_validation_recovery_v013.log"][1]
        or summary.get("validation_process", {}).get("stdout_sha256")
        != RUNTIME_V013_RESULT_FILES[
            "fresh_process_validation_recovery_v013.stdout.log"][1]
        or summary.get("validation_process", {}).get("stderr_sha256")
        != RUNTIME_V013_RESULT_FILES[
            "fresh_process_validation_recovery_v013.stderr.log"][1]
    ):
        raise ContractError("runtime V013 summary-to-five-file hash binding drift")
    return {
        "run_id": RUNTIME_RECOVERY_V013_RUN_ID,
        "run_root": relative(root),
        "files": evidence,
        "fresh_validation_receipt":
            evidence["fresh_process_validation_receipt_recovery_v013.json"],
        "lane_summary": evidence["lane_summary_recovery_v013.json"],
        "package_sha256": packages,
        "historical_v013_source_snapshot": source,
        "historical_v013_protected_snapshot": protected,
        "historical_v013_prepared_lane_snapshot": prepared_lane,
        "asset_registry_cache": cache,
        "legacy_asset_registry_cache_absence": legacy,
        "validation_process_id": process_id,
        "import_process_id": import_process_id,
        "vehicle_model_id": model[0],
        "production_recipe_id": model[1],
        "current_geometry_authority_id": model[2],
    }


def runtime_authority() -> dict:
    runtime_contract, contract_digest = sidecar(
        RUNTIME_CONTRACT, RUNTIME_CONTRACT_SHA, "approved vehicle runtime contract"
    )
    runtime_baseline, baseline_digest = sidecar(
        RUNTIME_BASELINE, RUNTIME_BASELINE_SHA, "approved vehicle runtime baseline"
    )
    recovery, recovery_digest = sidecar(
        RUNTIME_RECOVERY_V013_CONTRACT,
        RUNTIME_RECOVERY_V013_CONTRACT_SHA,
        "runtime recovery V013 contract",
    )
    incident = recovery.get("incident_chain", {})
    model = recovery.get("vehicle_model_identity", {})
    policy = recovery.get("policy", {})
    if (
        runtime_contract.get("$schema") != RUNTIME_CONTRACT_SCHEMA
        or runtime_contract.get("status") != RUNTIME_CONTRACT_STATUS
        or runtime_contract.get("destination", {}).get("namespace") != RUNTIME_DEST
        or runtime_contract.get("destination", {}).get("expected_package_count") != 11
        or runtime_baseline.get("$schema") != RUNTIME_BASELINE_SCHEMA
        or runtime_baseline.get("status") != RUNTIME_BASELINE_STATUS
        or runtime_baseline.get("contract", {}).get("sha256") != contract_digest
        or contract_digest != EXPECTED_RUNTIME_CONTRACT_SHA256
        or baseline_digest != EXPECTED_RUNTIME_BASELINE_SHA256
        or recovery.get("$schema") != RUNTIME_RECOVERY_V013_SCHEMA
        or recovery.get("status") != RUNTIME_RECOVERY_V013_STATUS
        or recovery_digest != EXPECTED_RUNTIME_RECOVERY_V013_CONTRACT_SHA256
        or incident.get("binding_sha256") != EXPECTED_RUNTIME_INCIDENT_CHAIN_SHA256
        or model.get("model_id") != "CAIRNWELL_2040"
        or model.get("production_recipe_id")
        != "CAIRNWELL_2040_DEVELOPMENT_RECIPE_V001"
        or model.get("current_geometry_authority_id")
        != "Cairnwell2040Runtime_v001_V009ImportedGeometry"
        or model.get("lifecycle")
        != "DEVELOPMENT__APPROVED_FOR_GAME_BUILD__NOT_FINAL_ART"
        or model.get("final_release_visual_lock_claimed") is not False
        or policy.get("validation_only_recovery") is not True
        or policy.get("existing_v009_packages_are_immutable") is not True
        or policy.get("panel_module_namespace_or_packages_authorized") is not False
        or policy.get("unreal_launch_authorized_by_freeze") is not False
    ):
        raise ContractError("approved runtime V013 authority identity/policy drift")
    for key, expected_path in (
        ("contract", RUNTIME_CONTRACT), ("contract_sidecar", RUNTIME_CONTRACT_SHA),
        ("baseline", RUNTIME_BASELINE), ("baseline_sidecar", RUNTIME_BASELINE_SHA),
    ):
        row(expected_path, recovery.get("original_authorities", {}).get(key))
    passed = runtime_v013_pass(recovery_digest)
    packages = passed["package_sha256"]
    expected_packages = runtime_contract["destination"]["expected_package_paths"]
    if list(packages) != sorted(expected_packages, key=str.casefold):
        raise ContractError("runtime V013 package order/closure differs from original contract")
    for package, digest in packages.items():
        disk = PROJECT / ("Content/" + package.removeprefix("/Game/") + ".uasset")
        if sha256(disk) != str(digest).upper():
            raise ContractError(f"approved runtime package hash drift: {package}")
    materials = {}
    for role, (asset_name, package_relative) in RUNTIME_MATERIALS.items():
        package = f"{RUNTIME_DEST}/{package_relative}"
        if package not in packages:
            raise ContractError(f"required runtime material missing from V013 closure: {role}")
        materials[role] = {
            "asset_name": asset_name,
            "package_path": package,
            "object_path": f"{package}.{asset_name}",
            "package_sha256": packages[package],
        }
    return {
        "destination_namespace": RUNTIME_DEST,
        "contract": row(RUNTIME_CONTRACT),
        "contract_sidecar": row(RUNTIME_CONTRACT_SHA),
        "contract_sha256": contract_digest,
        "baseline": row(RUNTIME_BASELINE),
        "baseline_sidecar": row(RUNTIME_BASELINE_SHA),
        "baseline_sha256": baseline_digest,
        "recovery_v013_contract": row(RUNTIME_RECOVERY_V013_CONTRACT),
        "recovery_v013_contract_sidecar": row(RUNTIME_RECOVERY_V013_CONTRACT_SHA),
        "recovery_v013_contract_sha256": recovery_digest,
        "incident_chain_sha256": EXPECTED_RUNTIME_INCIDENT_CHAIN_SHA256,
        "recovery_v013_run_id": passed["run_id"],
        "recovery_v013_run_root": passed["run_root"],
        "recovery_v013_result_files": passed["files"],
        "fresh_validation_receipt": passed["fresh_validation_receipt"],
        "lane_summary": passed["lane_summary"],
        "package_sha256": packages,
        "materials": materials,
        "historical_v013_source_snapshot": passed["historical_v013_source_snapshot"],
        "historical_v013_protected_snapshot":
            passed["historical_v013_protected_snapshot"],
        "historical_v013_prepared_lane_snapshot":
            passed["historical_v013_prepared_lane_snapshot"],
        "asset_registry_cache": passed["asset_registry_cache"],
        "legacy_asset_registry_cache_absence":
            passed["legacy_asset_registry_cache_absence"],
        "validation_process_id": passed["validation_process_id"],
        "import_process_id": passed["import_process_id"],
        "vehicle_model_id": passed["vehicle_model_id"],
        "production_recipe_id": passed["production_recipe_id"],
        "current_geometry_authority_id": passed["current_geometry_authority_id"],
        "lifecycle": "DEVELOPMENT__APPROVED_FOR_GAME_BUILD__NOT_FINAL_ART",
        "final_release_visual_lock_claimed": False,
        "geometry_revisionable": True,
        "historical_v013_project_snapshots_are_receipt_evidence_not_live_baseline": True,
        "current_project_authority_is_the_new_panel_baseline": True,
        "persisted_dependency_closure_verified": True,
        "all_package_hashes_unchanged": True,
        "cache_and_legacy_surfaces_unchanged": True,
        "no_build_tool_invoked": True,
    }


def source_file_from_manifest(value, field: str) -> dict:
    if not isinstance(value, dict):
        raise ContractError(f"{field} must be a file authority object")
    path = (PROJECT / str(value.get("path", ""))).resolve()
    try:
        path.relative_to(SOURCE_ROOT.resolve())
    except ValueError as exc:
        raise ContractError(f"{field} escapes the isolated panel source root") from exc
    return row(path, value)


def normalise_lod(panel_id: str, expected_index: int, value: dict) -> dict:
    if not isinstance(value, dict) or int(value.get("lod", -1)) != expected_index:
        raise ContractError(f"{panel_id} must declare ordered LOD0/1/2")
    fbx = source_file_from_manifest(value.get("fbx"), f"{panel_id}:LOD{expected_index}:fbx")
    glb = source_file_from_manifest(value.get("glb"), f"{panel_id}:LOD{expected_index}:glb")
    if Path(fbx["path"]).suffix.casefold() != ".fbx" or Path(glb["path"]).suffix.casefold() != ".glb":
        raise ContractError(f"{panel_id}:LOD{expected_index} must pin FBX and GLB evidence")
    triangles = int(value.get("triangles", 0))
    vertices = int(value.get("vertices", 0))
    uv_channels = int(value.get("uv_channels", -1))
    degenerates = int(value.get("degenerate_triangles", -1))
    duplicates = int(value.get("duplicate_triangles", -1))
    zero_length = int(value.get("zero_length_edges", -1))
    boundary = int(value.get("boundary_edges", -1))
    nonmanifold = int(value.get("nonmanifold_edges", -1))
    self_intersections = int(value.get("self_intersection_pairs", -1))
    if (
        triangles <= 0
        or vertices <= 0
        or uv_channels != 1
        or degenerates != 0
        or duplicates != 0
        or zero_length != 0
        or boundary != 0
        or nonmanifold != 0
        or self_intersections != 0
    ):
        raise ContractError(
            f"{panel_id}:LOD{expected_index} triangle/vertex/one-UV/closed-clean-topology gate failed"
        )
    minimum = vector(value.get("bounds_min_cm"), f"{panel_id}:LOD{expected_index}:bounds_min_cm")
    maximum = vector(value.get("bounds_max_cm"), f"{panel_id}:LOD{expected_index}:bounds_max_cm")
    pivot = vector(value.get("pivot_cm"), f"{panel_id}:LOD{expected_index}:pivot_cm")
    if pivot != [0.0, 0.0, 0.0]:
        raise ContractError(f"{panel_id}:LOD{expected_index} was recentered off the shared car datum")
    if any(maximum[axis] <= minimum[axis] for axis in range(3)):
        raise ContractError(f"{panel_id}:LOD{expected_index} has invalid bounds")
    if any(
        minimum[axis] < CAR_ENVELOPE_MIN_CM[axis] - BOUNDS_TOLERANCE_CM
        or maximum[axis] > CAR_ENVELOPE_MAX_CM[axis] + BOUNDS_TOLERANCE_CM
        for axis in range(3)
    ):
        raise ContractError(f"{panel_id}:LOD{expected_index} escapes the fitted car envelope")
    slots = value.get("material_slots")
    if slots != [SEMANTIC_SLOT]:
        raise ContractError(f"{panel_id}:LOD{expected_index} must have one semantic material slot")
    provenance = value.get("source_face_provenance")
    if (
        not isinstance(provenance, dict)
        or provenance.get("method") != "PARAMETRIC_NATIVE_AUTHORED_V002"
        or provenance.get("v005_body_faces_copied") is not False
        or provenance.get("v005_role") != "DIMENSIONAL_SILHOUETTE_REFERENCE_ONLY"
        or not math.isfinite(float(provenance.get("nominal_inward_thickness_mm", math.nan)))
        or float(provenance.get("nominal_inward_thickness_mm", 0.0)) <= 0.0
    ):
        raise ContractError(f"{panel_id}:LOD{expected_index} parametric/v005-reference provenance drift")
    roundtrip = value.get("roundtrip")
    if not isinstance(roundtrip, dict) or set(roundtrip) != {"fbx", "glb"}:
        raise ContractError(f"{panel_id}:LOD{expected_index} lacks exact FBX/GLB roundtrip evidence")
    checked_roundtrip = {}
    for format_name in ("fbx", "glb"):
        evidence = roundtrip.get(format_name)
        if not isinstance(evidence, dict):
            raise ContractError(f"{panel_id}:LOD{expected_index}:{format_name} roundtrip row drift")
        roundtrip_min = vector(
            evidence.get("bounds_min_cm"),
            f"{panel_id}:LOD{expected_index}:{format_name}:bounds_min_cm",
        )
        roundtrip_max = vector(
            evidence.get("bounds_max_cm"),
            f"{panel_id}:LOD{expected_index}:{format_name}:bounds_max_cm",
        )
        origins = evidence.get("origins_cm")
        if (
            int(evidence.get("mesh_objects", -1)) != 1
            or int(evidence.get("triangles", -1)) != triangles
            or int(evidence.get("vertices", 0)) <= 0
            or (format_name == "fbx" and int(evidence.get("vertices", -1)) != vertices)
            or int(evidence.get("uv_channels_min", -1)) != 1
            or origins != [[0.0, 0.0, 0.0]]
            or evidence.get("material_slots_canonical") != [SEMANTIC_SLOT]
            or any(
                abs(roundtrip_min[axis] - minimum[axis]) > ROUNDTRIP_BOUNDS_TOLERANCE_CM
                or abs(roundtrip_max[axis] - maximum[axis]) > ROUNDTRIP_BOUNDS_TOLERANCE_CM
                for axis in range(3)
            )
        ):
            raise ContractError(
                f"{panel_id}:LOD{expected_index}:{format_name} roundtrip topology/datum/slot drift"
            )
        checked_roundtrip[format_name] = {
            "mesh_objects": 1,
            "triangles": triangles,
            "vertices": int(evidence["vertices"]),
            "uv_channels_min": 1,
            "bounds_min_cm": roundtrip_min,
            "bounds_max_cm": roundtrip_max,
            "origins_cm": [[0.0, 0.0, 0.0]],
            "material_slots_canonical": [SEMANTIC_SLOT],
        }
    return {
        "lod": expected_index,
        "source": fbx,
        "portable_evidence": glb,
        "triangles": triangles,
        "source_vertices": vertices,
        "uv_channels": 1,
        "degenerate_triangles": 0,
        "duplicate_triangles": 0,
        "zero_length_edges": 0,
        "boundary_edges": 0,
        "nonmanifold_edges": 0,
        "self_intersection_pairs": 0,
        "material_slots": [SEMANTIC_SLOT],
        "expected_unreal_bounds": {
            "minimum_cm": minimum,
            "maximum_cm": maximum,
            "dimensions_cm": [round(maximum[i] - minimum[i], 6) for i in range(3)],
            "pivot_cm": [0.0, 0.0, 0.0],
        },
        "roundtrip": checked_roundtrip,
        "source_face_provenance": provenance,
    }


def object_record(panel_id: str) -> dict:
    asset_name = EXPECTED_ASSET_NAMES[panel_id]
    package = f"{DEST}/Meshes/{asset_name}"
    return {
        "panel_id": panel_id,
        "asset_name": asset_name,
        "package_path": package,
        "object_path": f"{package}.{asset_name}",
        "disk_path": "Content/" + package.removeprefix("/Game/") + ".uasset",
    }


def normalise_module(panel_id: str, value: dict, materials: dict) -> dict:
    if (
        not isinstance(value, dict)
        or value.get("role") != panel_id
        or value.get("asset_name") != EXPECTED_SOURCE_ASSET_NAMES[panel_id]
        or value.get("unreal_destination_asset_name") != EXPECTED_ASSET_NAMES[panel_id]
        or value.get("material_role") != DEFAULT_MATERIAL_ROLE
        or value.get("shared_origin") is not True
    ):
        raise ContractError(f"{panel_id} exact v002 source asset name drift")
    lod_values = value.get("lods")
    if not isinstance(lod_values, list) or len(lod_values) != 3:
        raise ContractError(f"{panel_id} must provide exactly three authored LODs")
    lods = [normalise_lod(panel_id, index, lod_values[index]) for index in range(3)]
    chain = [lod["triangles"] for lod in lods]
    if not chain[0] > chain[1] > chain[2] > 0:
        raise ContractError(f"{panel_id} lacks strict descending authored triangles")
    if value.get("material_slot") != SEMANTIC_SLOT:
        raise ContractError(f"{panel_id} semantic slot identity drift")
    result = object_record(panel_id)
    result.update({
        "source_authority_version": SOURCE_AUTHORITY_VERSION,
        "source_asset_name": EXPECTED_SOURCE_ASSET_NAMES[panel_id],
        "source_material_role": DEFAULT_MATERIAL_ROLE,
        "unreal_destination_version": UNREAL_DESTINATION_VERSION,
        "lods": lods,
        "triangle_chain": chain,
        "material_slots": [SEMANTIC_SLOT],
        "material_bindings": {
            "default": materials[DEFAULT_MATERIAL_ROLE]["object_path"],
            "available_stage_roles": {
                role: materials[role]["object_path"] for role in RUNTIME_MATERIALS
            },
        },
        "nanite_enabled": False,
        "collision": {
            "simple_count": 0,
            "convex_count": 0,
            "trace_flag": "CTF_USE_SIMPLE_AS_COMPLEX",
        },
        "has_navigation_data": False,
        "shared_origin_preserved": True,
        "fitted_car_envelope_cm": {
            "minimum": CAR_ENVELOPE_MIN_CM,
            "maximum": CAR_ENVELOPE_MAX_CM,
        },
    })
    return result


def build_payload(manifest: dict) -> dict:
    if manifest.get("$schema", manifest.get("schema")) != PANEL_SCHEMA:
        raise ContractError("panel source manifest schema drift")
    if manifest.get("status") != PANEL_STATUS:
        raise ContractError(
            "panel manifest is not root-approved; pending sources cannot freeze an Unreal contract"
        )
    source_authority = source_freeze_authority(manifest)
    if SOURCE_MANIFEST.resolve() != (PROJECT / relative(SOURCE_MANIFEST)).resolve():
        raise ContractError("exact panel manifest path drift")
    approval = manifest.get("approval")
    if (
        not isinstance(approval, dict)
        or approval.get("root_visual_gate") != "APPROVED"
        or approval.get("approved_direction")
        != "FUTURISTIC_SOLID_COLOUR_FOUR_DOOR_ESTATE_CROSSOVER"
        or approval.get("unreal_import_or_promotion_authorized") is not False
    ):
        raise ContractError("v002 root visual approval/source-only freeze gate drift")
    selected = manifest.get("selected_source")
    if (
        not isinstance(selected, dict)
        or selected.get("candidate") != "Cairnwell2040ParametricAuthored"
        or selected.get("version") != SOURCE_AUTHORITY_VERSION
        or selected.get("body_geometry") != "PARAMETRIC_NATIVE_AUTHORING"
        or selected.get("v005_geometry_role") != "DIMENSIONAL_SILHOUETTE_REFERENCE_ONLY"
        or selected.get("v005_body_faces_copied") is not False
        or selected.get("rolling_gear_authority") != "ProductionCandidate_v005"
    ):
        raise ContractError("panel modules must use exact parametric v002 geometry/v005 reference roles")
    selected_manifest = row(V005_MANIFEST, selected.get("manifest"))
    if selected_manifest["sha256"] != EXPECTED_V005_MANIFEST_SHA256:
        raise ContractError("selected v005 silhouette/rolling-gear authority hash drift")
    if "ProductionCandidate_v006" in json.dumps(manifest):
        raise ContractError("panel source authority may not reuse v006")
    if (
        manifest.get("source_authority_version") != SOURCE_AUTHORITY_VERSION
        or manifest.get("unreal_destination_version") != UNREAL_DESTINATION_VERSION
    ):
        raise ContractError("source v002 to Unreal destination v001 version seam drift")
    shared = manifest.get("shared_datum")
    if (
        not isinstance(shared, dict)
        or shared.get("forward_axis") != "+X"
        or shared.get("right_axis") != "+Y"
        or shared.get("up_axis") != "+Z"
        or vector(shared.get("pivot_cm"), "shared_datum:pivot_cm") != [0.0, 0.0, 0.0]
        or vector(shared.get("canonical_dimensions_cm"), "shared_datum:canonical_dimensions_cm")
        != CAR_DIMENSIONS_CM
        or float(shared.get("tyre_contact_z_cm", math.inf)) != 0.0
        or vector(shared.get("car_envelope_min_cm"), "shared_datum:car_envelope_min_cm")
        != CAR_ENVELOPE_MIN_CM
        or vector(shared.get("car_envelope_max_cm"), "shared_datum:car_envelope_max_cm")
        != CAR_ENVELOPE_MAX_CM
    ):
        raise ContractError("full-car shared zero datum or fitted envelope drift")
    fitted = manifest.get("fitted_car_envelope")
    if (
        not isinstance(fitted, dict)
        or vector(fitted.get("min_cm"), "fitted_car_envelope:min_cm")
        != CAR_ENVELOPE_MIN_CM
        or vector(fitted.get("max_cm"), "fitted_car_envelope:max_cm")
        != CAR_ENVELOPE_MAX_CM
        or vector(fitted.get("dimensions_cm"), "fitted_car_envelope:dimensions_cm")
        != CAR_DIMENSIONS_CM
    ):
        raise ContractError("independent fitted-car envelope evidence drift")
    runtime = runtime_authority()
    material_contract = manifest.get("material_contract")
    if (
        not isinstance(material_contract, dict)
        or material_contract.get("slot") != SEMANTIC_SLOT
        or material_contract.get("default_material_role") != DEFAULT_MATERIAL_ROLE
        or tuple(material_contract.get("allowed_material_roles", [])) != tuple(RUNTIME_MATERIALS)
        or material_contract.get("duplicate_textures_or_materials") is not False
        or material_contract.get("solid_colour_style") is not True
        or material_contract.get("roughness_style") != "SUBTLE_ONLY"
    ):
        raise ContractError("panel material contract must reuse the exact runtime three-material closure")
    modules_raw = manifest.get("modules")
    if (
        not isinstance(modules_raw, list)
        or len(modules_raw) != 11
        or tuple(manifest.get("module_order", [])) != PANEL_IDS
        or tuple(item.get("role") for item in modules_raw if isinstance(item, dict)) != PANEL_IDS
    ):
        raise ContractError("manifest must declare the exact 11 gameplay panel IDs in order")
    modules_by_id = {item["role"]: item for item in modules_raw}
    if len(modules_by_id) != 11:
        raise ContractError("manifest panel role list contains a duplicate")
    modules = {
        panel_id: normalise_module(panel_id, modules_by_id[panel_id], runtime["materials"])
        for panel_id in PANEL_IDS
    }
    fbx_paths = [lod["source"]["path"] for module in modules.values() for lod in module["lods"]]
    glb_paths = [lod["portable_evidence"]["path"] for module in modules.values() for lod in module["lods"]]
    if len(fbx_paths) != 33 or len(set(fbx_paths)) != 33:
        raise ContractError("panel closure must provide 33 distinct authored FBX files")
    if len(glb_paths) != 33 or len(set(glb_paths)) != 33:
        raise ContractError("panel closure must provide 33 distinct GLB evidence files")
    audit = source_authority["production_audit_payload"]
    if (
        audit.get("panel_lods") != {
            panel_id: modules_by_id[panel_id]["lods"] for panel_id in PANEL_IDS
        }
        or audit.get("lod_audit") != manifest.get("lod_audit")
    ):
        raise ContractError("production audit does not duplicate the exact 11x3 manifest evidence")
    gap = manifest.get("gap_audit")
    gap_names = (
        "front_fender_to_front_door",
        "front_door_to_rear_door",
        "rear_door_to_rear_quarter",
        "hood_nose_to_front_fender_inner_surface",
    )
    if (
        not isinstance(gap, dict)
        or gap.get("units") != "mm"
        or gap.get("required_range_mm") != [10.0, 15.0]
        or gap.get("status") != "PASS"
        or any(not 10.0 <= float(gap.get(name, math.nan)) <= 15.0 for name in gap_names)
    ):
        raise ContractError("fitted panel gap audit drift")
    intersections = manifest.get("intersection_audit")
    if (
        not isinstance(intersections, dict)
        or intersections.get("status") != "PASS"
        or int(intersections.get("fitted_panel_pair_triangle_overlaps_all_lods", -1)) != 0
        or int(intersections.get("panel_self_intersection_pairs_all_lods", -1)) != 0
    ):
        raise ContractError("panel fitted/self-intersection audit drift")
    lod_audit = manifest.get("lod_audit")
    if not isinstance(lod_audit, list) or len(lod_audit) != 3:
        raise ContractError("panel fitted LOD audit must contain exact LOD0/1/2")
    for lod_index, item in enumerate(lod_audit):
        expected_triangles = sum(
            modules[panel_id]["lods"][lod_index]["triangles"] for panel_id in PANEL_IDS
        )
        if (
            not isinstance(item, dict)
            or int(item.get("lod", -1)) != lod_index
            or item.get("fitted_panel_overlap_pairs") != []
            or int(item.get("panel_triangles", -1)) != expected_triangles
        ):
            raise ContractError(f"panel fitted LOD{lod_index} overlay/triangle audit drift")
    visual = manifest.get("visual_approval")
    if (
        not isinstance(visual, dict)
        or visual.get("status") != "APPROVED_BY_ROOT__FREEZE_AUTHORIZED"
    ):
        raise ContractError("fitted/rack/progression visual approval is absent")
    expected_visual_keys = {
        "hero", "front", "side", "rear", "fitted_overlay", "fitted_overlay_side",
        "rack_exploded", "assembly_progression", "flat_wire",
    }
    if set(visual) != expected_visual_keys | {"status", "stage_order"}:
        raise ContractError("visual approval evidence key closure drift")
    expected_stages = [
        "BODY_FRAME", "FENDERS_AND_QUARTERS", "FOUR_DOORS", "HOOD",
        "ROOF_AND_TAILGATE", "GLAZING_LAMPS_TRIM", "ROLLING_FINISHED",
    ]
    if visual.get("stage_order") != expected_stages:
        raise ContractError("assembly visual stage order drift")
    visual_rows = {
        key: source_file_from_manifest(visual[key], f"visual_approval:{key}")
        for key in sorted(expected_visual_keys)
    }
    source_blend = source_file_from_manifest(manifest.get("source_blend"), "source_blend")
    if manifest.get("supporting_module_contract", {}).get("separate_from_panel_import_contract") is not True:
        raise ContractError("supporting body/trim/rolling meshes must remain outside the 11-panel import")
    sentinel = manifest.get("protected_v005_sentinel_verification")
    if not isinstance(sentinel, dict) or sentinel.get("byte_exact") is not True:
        raise ContractError("protected v005 byte-exact sentinel evidence drift")
    source_files = {
        item["path"]: item
        for item in source_authority["frozen_inventory_before_receipt"]
    }
    source_files[source_authority["freeze_receipt"]["path"]] = source_authority["freeze_receipt"]
    source_files[selected_manifest["path"]] = selected_manifest
    if len(source_files) != 111 or source_blend["path"] not in source_files:
        raise ContractError("exact 110-file v002 freeze plus selected v005 manifest closure drift")
    expected_packages = [modules[panel_id]["package_path"] for panel_id in PANEL_IDS]
    lane_files = [
        "Scripts/prepare_cairnwell_2040_panel_modules_v001_contract.py",
        "Scripts/prepare_cairnwell_2040_panel_modules_v001_baseline.py",
        "Scripts/cairnwell_2040_panel_modules_v001.py",
        "Scripts/import_cairnwell_2040_panel_modules_v001.py",
        "Scripts/validate_cairnwell_2040_panel_modules_fresh_process_v001.py",
        "Scripts/run_cairnwell_2040_panel_modules_import_lane_v001.ps1",
        "Scripts/tests/test_cairnwell_2040_panel_modules_import_lane_v001.py",
        "Docs/OneFactory/CAIRNWELL_2040_PANEL_MODULES_V001_UNREAL_IMPORT_LANE.md",
    ]
    return {
        "$schema": "lineboss/cairnwell-2040-panel-modules-v001/unreal-import-contract/v1",
        "status": CONTRACT_STATUS,
        "provenance": {
            "description": (
                "approved parametric-authored v002 panels using v005 only as dimensional "
                "silhouette and rolling-gear reference; rejected crumpled/preview panel "
                "passes and loose Meshy panel substitutes remain preserved but excluded"
            ),
            "source_authority_version": SOURCE_AUTHORITY_VERSION,
            "unreal_destination_version": UNREAL_DESTINATION_VERSION,
            "selected_candidate": "Cairnwell2040ParametricAuthored",
            "selected_version": SOURCE_AUTHORITY_VERSION,
            "geometry_method": "PARAMETRIC_NATIVE_AUTHORING",
            "v005_geometry_role": "DIMENSIONAL_SILHOUETTE_REFERENCE_ONLY",
            "v005_body_faces_copied": False,
            "manifest": source_authority["manifest"],
            "production_audit": source_authority["production_audit"],
            "freeze_receipt": source_authority["freeze_receipt"],
            "frozen_v002_file_count": 110,
            "v005_manifest": selected_manifest,
            "source_files": [source_files[key] for key in sorted(source_files, key=str.casefold)],
            "visual_approval": {
                "status": "APPROVED_BY_ROOT__FREEZE_AUTHORIZED",
                "stage_order": expected_stages,
                "evidence": visual_rows,
            },
            "gap_audit": gap,
            "intersection_audit": intersections,
            "lod_audit": lod_audit,
            "source_blend": source_blend,
            "roundtrip_evidence_required_for_all_33_lods": True,
            "protected_v005_byte_exact": True,
        },
        "destination": {
            "namespace": DEST,
            "disk_root": relative(DEST_DISK),
            "must_be_absent_before_run": True,
            "expected_mesh_count": 11,
            "expected_authored_lod_count": 33,
            "expected_texture_count": 0,
            "expected_material_count": 0,
            "expected_package_count": 11,
            "expected_source_fbx_count": 33,
            "expected_package_paths": expected_packages,
        },
        "shared_datum": {
            "forward_axis": "+X",
            "right_axis": "+Y",
            "up_axis": "+Z",
            "pivot_cm": [0.0, 0.0, 0.0],
            "canonical_dimensions_cm": CAR_DIMENSIONS_CM,
            "tyre_contact_z_cm": 0.0,
            "car_envelope_min_cm": CAR_ENVELOPE_MIN_CM,
            "car_envelope_max_cm": CAR_ENVELOPE_MAX_CM,
        },
        "runtime_authority": runtime,
        "project_authority_boundary": {
            "runtime_v013_project_snapshots_role":
                "HISTORICAL_VALIDATION_EVIDENCE_ONLY",
            "runtime_v013_source_snapshot":
                runtime["historical_v013_source_snapshot"],
            "runtime_v013_protected_snapshot":
                runtime["historical_v013_protected_snapshot"],
            "runtime_v013_prepared_lane_snapshot":
                runtime["historical_v013_prepared_lane_snapshot"],
            "current_project_authority":
                "NEW_PANEL_BASELINE_FULL_PROJECT_SNAPSHOT",
            "authorized_intervening_source_evolution":
                "PAINT_PRESENTATION_SOURCE_EVOLUTION",
            "authorized_intervening_source_evolution_is_not_future_drift_permission": True,
            "unrelated_future_drift_authorized": False,
        },
        "material_reuse": {
            "semantic_slot": SEMANTIC_SLOT,
            "default_role": DEFAULT_MATERIAL_ROLE,
            "materials": runtime["materials"],
            "new_texture_count": 0,
            "new_material_count": 0,
        },
        "modules": modules,
        "import_contract": {
            "fresh_only": True,
            "editor_bootstrap_world": "/Engine/Maps/Entry.Entry",
            "project_map_load_save_authorized": False,
            "editor_startup_map_override": MAPLESS_STARTUP_OVERRIDE,
            "replace_existing": False,
            "combine_meshes": True,
            "import_materials_from_fbx": False,
            "import_textures_from_fbx": False,
            "import_animations": False,
            "generate_lightmap_uvs": False,
            "auto_generate_collision": False,
            "remove_degenerates": False,
            "nanite_enabled": False,
            "has_navigation_data": False,
            "collision_trace_flag": "CTF_USE_SIMPLE_AS_COMPLEX",
            "lod_screen_sizes": [1.0, 0.35, 0.12],
            "auto_compute_lod_screen_size": False,
            "bounds_tolerance_cm": BOUNDS_TOLERANCE_CM,
            "source_roundtrip_bounds_tolerance_cm": ROUNDTRIP_BOUNDS_TOLERANCE_CM,
            "pivot_tolerance_cm": 0.01,
            "no_asset_registry_cache_write_command_line_flag":
                "-NoAssetRegistryCacheWrite",
            "ubt_startup_guard_environment": {
                "name": "UE_SKIP_UBT_SDK_SETUP",
                "required_value": "1",
            },
            "explicit_quit_editor_forbidden": True,
            "natural_execute_python_script_exit_required": True,
            "strict_exit_zero_no_fatal_ensure_or_ubt_log_required": True,
        },
        "lane_files_to_pin_when_baseline_is_cut": lane_files,
        "policy": {
            "overwrite_reimport_delete_authorized": False,
            "map_load_save_authorized": False,
            "runtime_binding_or_map_promotion_authorized": False,
            "automatic_partial_cleanup": False,
            "content_writes_authorized_only_inside_fresh_destination": True,
            "source_config_maps_saves_writes_authorized": False,
            "runtime_authority_mutation_authorized": False,
            "baseline_must_be_cut_after_contract_freeze_and_before_unreal": True,
            "runtime_authority_must_be_exact_v013_run_not_latest_pass": True,
            "asset_registry_cache_and_legacy_surfaces_must_remain_exact": True,
            "development_geometry_is_revisionable_behind_stable_contract": True,
            "final_release_visual_lock_claimed": False,
            "powershell_package_map_parsing_authorized": False,
            "python_strict_duplicate_key_result_validation_required": True,
            "post_v013_authorized_source_evolution_must_be_frozen_by_panel_baseline": True,
            "historical_v013_project_snapshot_may_not_replace_current_panel_baseline": True,
            "unrelated_post_panel_baseline_drift_authorized": False,
        },
    }


def create(manifest: Path, acknowledgement: str) -> None:
    if acknowledgement != ACK_TOKEN:
        raise ContractError("exact panel contract-freeze acknowledgement missing")
    if manifest.resolve() != SOURCE_MANIFEST.resolve():
        raise ContractError("--manifest must be the exact isolated panel manifest")
    if OUTPUT.exists() or OUTPUT_SHA.exists():
        raise ContractError("refusing to overwrite an existing panel contract or sidecar")
    if DEST_DISK.exists():
        raise ContractError("fresh panel destination already exists")
    if AUDIT_ROOT.exists():
        raise ContractError("one-shot panel audit root already exists")
    if not manifest.is_file():
        raise ContractError("approved panel source manifest is absent")
    payload = build_payload(strict_json_file(manifest, "approved panel source manifest"))
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    digest = sha256(OUTPUT)
    OUTPUT_SHA.write_text(f"{digest}  {OUTPUT.name}\n", encoding="ascii")
    print("PASS__CAIRNWELL_2040_PANEL_MODULES_V001_CONTRACT_FROZEN")
    print(digest)


def verify() -> None:
    payload, digest = sidecar(OUTPUT, OUTPUT_SHA, "panel import contract")
    if DEST_DISK.exists() or AUDIT_ROOT.exists():
        raise ContractError(
            "pre-baseline contract verification requires absent destination and audit root"
        )
    if not SOURCE_MANIFEST.is_file():
        raise ContractError("approved panel source manifest is absent")
    rebuilt = build_payload(strict_json_file(SOURCE_MANIFEST, "approved panel source manifest"))
    if payload != rebuilt:
        raise ContractError("source/runtime authorities no longer reproduce the frozen panel contract")
    print("PASS__CAIRNWELL_2040_PANEL_MODULES_V001_CONTRACT_REVERIFIED")
    print(digest)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--acknowledgement", default="")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        verify()
    else:
        if args.manifest is None:
            raise ContractError("--manifest is required; implicit/older panel manifests are forbidden")
        create(args.manifest, args.acknowledgement)


if __name__ == "__main__":
    main()
