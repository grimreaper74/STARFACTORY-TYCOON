"""Standard-library guards shared by panel validation-only Recovery_v002."""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8").resolve()
CONTRACT = PROJECT / "Scripts/cairnwell_2040_panel_modules_recovery_v002_contract.json"
CONTRACT_SHA = CONTRACT.with_suffix(".sha256")
AUDIT_ROOT = PROJECT / (
    "Saved/Audits/OneFactory/Vehicles/Cairnwell2040PanelModules_v001/"
    "UnrealImportLane_v001"
)
RECOVERY_AUDIT_ROOT = AUDIT_ROOT / "Recovery_v002"
INCIDENT_ROOT = AUDIT_ROOT / "20260815T182842Z-0205ac3e"
DEST_ROOT = PROJECT / (
    "Content/LineBoss/Factory/OneFactory/v001/Vehicles/"
    "Cairnwell2040PanelModules_v001"
)
RUN_ROOT_ENV = "LINEBOSS_CAIRNWELL_2040_PANEL_MODULES_RECOVERY_V002_RUN_ROOT"
ACK_ENV = "LINEBOSS_CAIRNWELL_2040_PANEL_MODULES_RECOVERY_V002_ACK"
ACK_TOKEN = "VALIDATE_CAIRNWELL_2040_PANEL_MODULES_RECOVERY_V002_ONCE"
CONTRACT_SCHEMA = (
    "lineboss/cairnwell-2040-panel-modules-v001/recovery-contract/v2"
)
CONTRACT_STATUS = (
    "FROZEN__CAIRNWELL_2040_PANEL_MODULES_V001_INCIDENT_BOUND__"
    "VALIDATION_ONLY_RECOVERY_V002__READY_FOR_ONE_FRESH_READ_ONLY_PROCESS"
)
RECEIPT = "fresh_process_validation_receipt_recovery_v002.json"
FAILURE = "fresh_process_validation_failure_recovery_v002.json"
SUMMARY = "lane_summary_recovery_v002.json"
CRC_EVIDENCE = "normal_crc_monitor_wait_recovery_v002.json"
RESULT_NAMES = {RECEIPT, FAILURE, SUMMARY, CRC_EVIDENCE}
EXPECTED_TOOL_PATHS = {
    "Scripts/prepare_cairnwell_2040_panel_modules_recovery_v002_contract.py",
    "Scripts/cairnwell_2040_panel_modules_recovery_v002.py",
    "Scripts/validate_cairnwell_2040_panel_modules_recovery_v002.py",
    "Scripts/verify_cairnwell_2040_panel_modules_recovery_v002.py",
    "Scripts/run_cairnwell_2040_panel_modules_recovery_v002.ps1",
    "Scripts/tests/test_cairnwell_2040_panel_modules_recovery_v002.py",
    "Docs/OneFactory/CAIRNWELL_2040_PANEL_MODULES_RECOVERY_V002.md",
}
INCIDENTAL_PATHS = (
    "Intermediate/PipInstall/extra_urls.txt",
    "Intermediate/PipInstall/Lib/site-packages/plugin_site_package.pth",
    "Intermediate/PipInstall/merged_requirements.in",
    "Intermediate/PipInstall/pyreqs_plugins.list",
    "Intermediate/PythonStub/unreal.py",
    "Saved/Autosaves/PackageRestoreData.json",
    (
        "Saved/Config/CrashReportClient/"
        "UECC-Windows-E2DB6C57421C4F327FB974B18EA18AC9/CrashReportClient.ini"
    ),
    "Saved/Config/WindowsEditor/EditorPerProjectUserSettings.ini",
    "Saved/SourceControl/UncontrolledChangelists.json",
    "Scripts/__pycache__/cairnwell_2040_panel_modules_v001.cpython-311.pyc",
)
CRASH_CONFIG_ROOT = PROJECT / "Saved/Config/CrashReportClient"


class RecoveryError(RuntimeError):
    """Fail-closed Recovery_v002 error."""


def strict_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise RecoveryError(f"duplicate JSON property forbidden: {key!r}")
        result[key] = value
    return result


def strict_json(path: Path, label: str) -> dict:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8-sig"), object_pairs_hook=strict_pairs
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise RecoveryError(f"{label} is unreadable") from exc
    if not isinstance(value, dict):
        raise RecoveryError(f"{label} must be a JSON object")
    return value


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
        raise RecoveryError(f"path escapes exact project: {path}") from exc


def file_row(path: Path) -> dict:
    if not path.is_file():
        raise RecoveryError(f"required file absent: {path}")
    stat = path.stat()
    return {
        "path": relative(path),
        "bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": sha256(path),
    }


def load_contract() -> tuple[dict, str]:
    if not CONTRACT.is_file() or not CONTRACT_SHA.is_file():
        raise RecoveryError("frozen Recovery_v002 contract pair is absent")
    digest = sha256(CONTRACT)
    if CONTRACT_SHA.read_text(encoding="ascii").strip().split() != [digest, CONTRACT.name]:
        raise RecoveryError("Recovery_v002 contract sidecar drift")
    payload = strict_json(CONTRACT, "Recovery_v002 contract")
    recovery = payload.get("recovery", {})
    policy = payload.get("policy", {})
    if (
        payload.get("$schema") != CONTRACT_SCHEMA
        or payload.get("status") != CONTRACT_STATUS
        or payload.get("incident_v001", {}).get("run_id")
        != "20260815T182842Z-0205ac3e"
        or payload.get("destination", {}).get("package_count") != 11
        or recovery.get("process_count") != 1
        or recovery.get("process_role")
        != "DISTINCT_FRESH_READ_ONLY_PERSISTED_VALIDATOR"
        or recovery.get("dependency_none_allowed_fresh_persisted_validation") is not False
        or recovery.get("normal_crc_monitor_natural_exit_wait_seconds") != 15
        or recovery.get("normal_crc_monitor_zero_process_stabilization_milliseconds") != 1000
        or policy.get("reimport_authorized") is not False
        or policy.get("content_write_authorized") is not False
        or policy.get("content_move_delete_authorized") is not False
        or policy.get("map_load_save_authorized") is not False
        or policy.get("only_recovery_audit_evidence_writes_authorized") is not False
        or policy.get("recovery_audit_plus_exactly_bounded_engine_ephemera_only") is not False
        or policy.get("authority_surfaces_plus_enumerated_known_ephemera_guarded") is not True
        or policy.get("zero_untracked_non_authority_ephemera_write_claimed") is not False
        or policy.get("existing_incidental_file_content_mutation_authorized") is not False
        or policy.get("existing_incidental_file_mtime_only_touch_authorized") is not True
        or recovery.get(
            "exact_existing_incidental_files_must_remain_path_byte_hash_exact"
        ) is not True
        or recovery.get("crash_reporter_config_new_file_maximum") != 1
        or recovery.get("python_bytecode_write_suppression_environment")
        != {"name": "PYTHONDONTWRITEBYTECODE", "value": "1"}
        or policy.get("python_bytecode_write_suppression_required") is not True
        or policy.get("uncontrolled_changelist_write_suppression_required") is not True
        or policy.get("python_stub_write_suppression_required") is not True
        or recovery.get("global_config_cache_write_suppression_flag") != "-nowrite"
        or policy.get("global_config_cache_write_suppression_required") is not True
    ):
        raise RecoveryError("Recovery_v002 identity/scope/policy drift")
    verify_tooling(payload)
    return payload, digest


def verify_incident(contract: dict) -> None:
    expected = contract["incident_v001"]["files"]
    files = {path.name: path for path in INCIDENT_ROOT.iterdir() if path.is_file()}
    if set(files) != set(expected) or any(path.is_dir() for path in INCIDENT_ROOT.iterdir()):
        raise RecoveryError("preserved v001 incident closure drift")
    for name, wanted in expected.items():
        actual = file_row(files[name])
        if any(actual[key] != wanted[key] for key in ("path", "bytes", "sha256")):
            raise RecoveryError(f"preserved v001 incident file drift: {name}")


def verify_tooling(contract: dict) -> None:
    rows = contract.get("tooling")
    if not isinstance(rows, list) or {item.get("path") for item in rows} != EXPECTED_TOOL_PATHS:
        raise RecoveryError("Recovery_v002 exact seven-file tooling closure drift")
    for wanted in rows:
        path = PROJECT / wanted["path"]
        actual = file_row(path)
        if any(actual[key] != wanted[key] for key in ("path", "bytes", "sha256")):
            raise RecoveryError("Recovery_v002 tooling file drift: " + wanted["path"])


def verify_preflight_topology() -> None:
    entries = list(AUDIT_ROOT.iterdir()) if AUDIT_ROOT.is_dir() else []
    if (
        len(entries) != 1
        or entries[0].resolve() != INCIDENT_ROOT.resolve()
        or not entries[0].is_dir()
        or RECOVERY_AUDIT_ROOT.exists()
    ):
        raise RecoveryError("Recovery_v002 preflight audit chronology/topology drift")


def verify_result_topology(root: Path) -> None:
    audit_entries = list(AUDIT_ROOT.iterdir()) if AUDIT_ROOT.is_dir() else []
    if (
        {item.name for item in audit_entries} != {INCIDENT_ROOT.name, "Recovery_v002"}
        or any(not item.is_dir() for item in audit_entries)
        or not RECOVERY_AUDIT_ROOT.is_dir()
    ):
        raise RecoveryError("Recovery_v002 post-run audit chronology/topology drift")
    recovery_entries = list(RECOVERY_AUDIT_ROOT.iterdir())
    if (
        len(recovery_entries) != 1
        or recovery_entries[0].resolve() != root.resolve()
        or not recovery_entries[0].is_dir()
    ):
        raise RecoveryError("Recovery_v002 must contain exactly one direct run child")


def package_files() -> dict:
    return {
        relative(path): {
            "bytes": path.stat().st_size,
            "mtime_ns": path.stat().st_mtime_ns,
            "sha256": sha256(path),
        }
        for path in sorted(
            (item for item in DEST_ROOT.rglob("*") if item.is_file()),
            key=lambda item: str(item).casefold(),
        )
    } if DEST_ROOT.is_dir() else {}


def destination_directories() -> list[str]:
    return sorted(
        (relative(path) for path in DEST_ROOT.rglob("*") if path.is_dir()),
        key=str.casefold,
    ) if DEST_ROOT.is_dir() else []


def verify_packages(contract: dict) -> dict:
    actual = package_files()
    expected = contract.get("destination", {})
    if (
        actual != expected.get("package_files")
        or len(actual) != 11
        or destination_directories() != expected.get("directory_paths")
    ):
        raise RecoveryError("exact 11-package Recovery_v002 closure drift")
    return actual


def canonical_hash(rows: list[dict]) -> str:
    compact = [
        {key: item[key] for key in ("path", "bytes", "mtime_ns", "sha256")}
        for item in sorted(rows, key=lambda value: value["path"].casefold())
    ]
    return hashlib.sha256(
        json.dumps(compact, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest().upper()


def incidental_snapshot() -> dict:
    rows = [file_row(PROJECT / path) for path in INCIDENTAL_PATHS]
    return {
        "file_count": len(rows),
        "inventory_sha256": canonical_hash(rows),
        "files": sorted(rows, key=lambda value: value["path"].casefold()),
        "pre_post_exact_path_byte_hash_invariance_required": True,
        "mtime_only_touches_must_be_explicitly_recorded": True,
    }


def incidental_content_rows(snapshot: dict) -> dict:
    return {
        item["path"]: {"bytes": item["bytes"], "sha256": item["sha256"]}
        for item in snapshot.get("files", [])
    }


def verify_incidental_content(contract: dict) -> dict:
    actual = incidental_snapshot()
    expected = contract.get("original_v001_incidental_project_writes", {})
    if (
        actual.get("file_count") != 10
        or expected.get("file_count") != 10
        or incidental_content_rows(actual) != incidental_content_rows(expected)
    ):
        raise RecoveryError("exact ten existing incidental-write path/byte/hash rows drift")
    return actual


def incidental_post_delta(contract: dict) -> dict:
    before = contract["original_v001_incidental_project_writes"]
    after = verify_incidental_content(contract)
    before_rows = {item["path"]: item for item in before["files"]}
    after_rows = {item["path"]: item for item in after["files"]}
    touched = [
        {
            "path": path,
            "before_mtime_ns": before_rows[path]["mtime_ns"],
            "after_mtime_ns": after_rows[path]["mtime_ns"],
            "bytes": after_rows[path]["bytes"],
            "sha256": after_rows[path]["sha256"],
        }
        for path in sorted(before_rows, key=str.casefold)
        if before_rows[path]["mtime_ns"] != after_rows[path]["mtime_ns"]
    ]
    return {
        "path_byte_hash_invariance_verified": True,
        "before_file_count": 10,
        "after_file_count": 10,
        "mtime_only_touch_count": len(touched),
        "mtime_only_touches": touched,
        "content_mutation_count": 0,
        "file_creation_deletion_count": 0,
    }


def crash_config_snapshot() -> dict:
    rows = [
        file_row(path) for path in CRASH_CONFIG_ROOT.rglob("*") if path.is_file()
    ] if CRASH_CONFIG_ROOT.is_dir() else []
    return {
        "file_count": len(rows),
        "inventory_sha256": canonical_hash(rows),
        "files": sorted(rows, key=lambda value: value["path"].casefold()),
    }


def verify_crash_config_preflight(contract: dict) -> dict:
    actual = crash_config_snapshot()
    if actual != contract.get("recovery_preflight_crash_reporter_config_tree"):
        raise RecoveryError("preflight CrashReportClient config tree drift")
    return actual


def verify_crash_config_post(contract: dict) -> dict:
    before = contract.get("recovery_preflight_crash_reporter_config_tree", {})
    after = crash_config_snapshot()
    before_rows = {item["path"]: item for item in before.get("files", [])}
    after_rows = {item["path"]: item for item in after.get("files", [])}
    if any(after_rows.get(path) != item for path, item in before_rows.items()):
        raise RecoveryError("existing CrashReportClient config row drift")
    new_paths = sorted(set(after_rows) - set(before_rows), key=str.casefold)
    if set(before_rows) - set(after_rows) or len(new_paths) > 1:
        raise RecoveryError("CrashReportClient config deletion/multiplicity drift")
    recovery_policy = contract["recovery"]
    pattern = re.compile(recovery_policy["crash_reporter_config_new_file_pattern"])
    new_rows = [after_rows[path] for path in new_paths]
    if any(
        not pattern.fullmatch(item["path"])
        or item["bytes"] != recovery_policy["crash_reporter_config_new_file_bytes"]
        or item["sha256"] != recovery_policy["crash_reporter_config_new_file_sha256"]
        for item in new_rows
    ):
        raise RecoveryError("new CrashReportClient config row escaped exact allowlist")
    return {
        "before_file_count": before.get("file_count"),
        "before_inventory_sha256": before.get("inventory_sha256"),
        "after_file_count": after.get("file_count"),
        "existing_rows_unchanged": True,
        "new_file_count": len(new_rows),
        "new_files": new_rows,
        "deleted_file_count": 0,
        "modified_existing_file_count": 0,
    }


def normalize_dependency_values(values, require_persisted: bool, package: str) -> set[str]:
    """Respect UE's Optional[Array[Name]] dependency API without weakening reload proof."""
    if values is None:
        if require_persisted:
            raise RecoveryError(
                "fresh persisted dependency query returned None: " + package
            )
        return set()
    if isinstance(values, (str, bytes, bytearray, dict)):
        raise RecoveryError("dependency query returned a non-array value: " + package)
    try:
        return {str(value) for value in values}
    except TypeError as exc:
        raise RecoveryError("dependency query returned a non-iterable value: " + package) from exc


def install_persisted_dependency_query(lane, unreal_module) -> dict:
    registry = unreal_module.AssetRegistryHelpers.get_asset_registry()
    options = unreal_module.AssetRegistryDependencyOptions(
        include_soft_package_references=True,
        include_hard_package_references=True,
        include_game_package_references=True,
        include_editor_only_package_references=False,
        include_searchable_names=False,
        include_soft_management_references=False,
        include_hard_management_references=False,
    )

    def persisted_dependencies(package: str) -> set[str]:
        raw = registry.get_dependencies(package, options)
        return normalize_dependency_values(raw, True, package)

    lane.project_dependencies = persisted_dependencies
    return {
        "include_soft_package_references": True,
        "include_hard_package_references": True,
        "include_game_package_references": True,
        "include_editor_only_package_references": False,
        "include_searchable_names": False,
        "include_soft_management_references": False,
        "include_hard_management_references": False,
    }


def run_root() -> Path:
    if os.environ.get(ACK_ENV) != ACK_TOKEN:
        raise RecoveryError("exact Recovery_v002 validation acknowledgement absent")
    raw = os.environ.get(RUN_ROOT_ENV, "")
    if not raw:
        raise RecoveryError("Recovery_v002 run-root environment absent")
    root = Path(raw).resolve()
    if root.parent != RECOVERY_AUDIT_ROOT.resolve() or not root.is_dir():
        raise RecoveryError("Recovery_v002 run root must be an existing direct child")
    if not root.name.startswith("2026") or len(root.name.rsplit("-", 1)[-1]) != 8:
        raise RecoveryError("Recovery_v002 run-id shape drift")
    return root


def write_json(path: Path, payload: dict) -> None:
    root = run_root()
    if path.parent.resolve() != root or path.name not in RESULT_NAMES or path.exists():
        raise RecoveryError("refusing Recovery_v002 evidence overwrite/path escape")
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()
