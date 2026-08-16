"""Freeze the incident-bound, validation-only Cairnwell panel recovery v002.

Offline standard Python only.  This tool never launches Unreal and writes only
the new recovery contract pair.  It binds the preserved failed v001 run, the
exact 11 packages it produced, the authoritative panel baseline v002, and the
normal CrashReportClient monitor evidence from the clean editor exit.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8").resolve()
OUTPUT = PROJECT / "Scripts/cairnwell_2040_panel_modules_recovery_v002_contract.json"
OUTPUT_SHA = OUTPUT.with_suffix(".sha256")
PANEL_CONTRACT = PROJECT / "Scripts/cairnwell_2040_panel_modules_v001_import_contract.json"
PANEL_CONTRACT_SHA = PANEL_CONTRACT.with_suffix(".sha256")
PANEL_BASELINE = PROJECT / "Scripts/cairnwell_2040_panel_modules_v001_import_baseline_v002.json"
PANEL_BASELINE_SHA = PANEL_BASELINE.with_suffix(".sha256")
BASELINE_TOOL = PROJECT / "Scripts/prepare_cairnwell_2040_panel_modules_v001_baseline.py"
AUDIT_ROOT = PROJECT / (
    "Saved/Audits/OneFactory/Vehicles/Cairnwell2040PanelModules_v001/"
    "UnrealImportLane_v001"
)
INCIDENT_RUN_ID = "20260815T182842Z-0205ac3e"
INCIDENT_ROOT = AUDIT_ROOT / INCIDENT_RUN_ID
RECOVERY_AUDIT_ROOT = AUDIT_ROOT / "Recovery_v002"
DEST_ROOT = PROJECT / (
    "Content/LineBoss/Factory/OneFactory/v001/Vehicles/"
    "Cairnwell2040PanelModules_v001"
)
CRASH_MONITOR_LOG = (
    Path.home() / "AppData/Local/CrashReportClient/Saved/Logs/CrashReportClient.log"
)
ACK_TOKEN = "FREEZE_CAIRNWELL_2040_PANEL_MODULES_VALIDATION_ONLY_RECOVERY_V002"
CONTRACT_SCHEMA = (
    "lineboss/cairnwell-2040-panel-modules-v001/recovery-contract/v2"
)
CONTRACT_STATUS = (
    "FROZEN__CAIRNWELL_2040_PANEL_MODULES_V001_INCIDENT_BOUND__"
    "VALIDATION_ONLY_RECOVERY_V002__READY_FOR_ONE_FRESH_READ_ONLY_PROCESS"
)
PANEL_CONTRACT_SHA256 = (
    "0EB0ED65D171A476D30F2F47BCEA9F63CF7CCE845369565AE6781ABE7CC35C2B"
)
PANEL_BASELINE_SHA256 = (
    "1EFDB747E4B07BF4EC1FB6AB239D63D0FD83608926967B020D439D1C11CA2EAE"
)
INCIDENT_FILES = {
    "import_failure_v001.json": {
        "bytes": 9962,
        "sha256": "5B24F5A392C6674159ED622C0CDD1C7BECD85C27C68665BE7263A123B98BD5D9",
    },
    "lane_summary_v001.json": {
        "bytes": 1236,
        "sha256": "E8D5D11CDD57AEC8BDE2DADF38D73C7F541E056DD945214656218B9B983729B8",
    },
    "unreal_import.log": {
        "bytes": 422152,
        "sha256": "BB185C7879895D56B50DAC725762997840ABBB9A5307E6D2C5456C6F9539F00F",
    },
    "unreal_import.stderr.log": {
        "bytes": 0,
        "sha256": "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855",
    },
    "unreal_import.stdout.log": {
        "bytes": 422200,
        "sha256": "5954E5FE13898C53D2F5D5BE92DCAAD1B72A788216CE16962098B07DB2A03B84",
    },
}
CRASH_MONITOR_LOG_SHA256 = (
    "53F8B4924FB338D48D677DD6551AAB5E05DA93A361BD1907AFEFD88FDEBD0E29"
)
CRASH_MONITOR_LOG_BYTES = 8134
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
INCIDENTAL_INCIDENT_ROWS = {
    "Intermediate/PipInstall/extra_urls.txt": (
        0, 1786818592906053200,
        "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855",
    ),
    "Intermediate/PipInstall/Lib/site-packages/plugin_site_package.pth": (
        0, 1786818592906053200,
        "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855",
    ),
    "Intermediate/PipInstall/merged_requirements.in": (
        0, 1786818592906053200,
        "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855",
    ),
    "Intermediate/PipInstall/pyreqs_plugins.list": (
        0, 1786818592902058700,
        "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855",
    ),
    "Intermediate/PythonStub/unreal.py": (
        37160016, 1786818622782174400,
        "5833F2AC4B0F4C1013B692974D223376BFD9F8E1A8AFFCFF3D04DF603351D9F3",
    ),
    "Saved/Autosaves/PackageRestoreData.json": (
        96, 1786818624643789000,
        "FDC2D5BEBF9CDEF10FE7088228558CB57FF12B0EA92EA114809E20FD2ADD5BB6",
    ),
    (
        "Saved/Config/CrashReportClient/"
        "UECC-Windows-E2DB6C57421C4F327FB974B18EA18AC9/CrashReportClient.ini"
    ): (
        239, 1786818548209949300,
        "CE69D7E7BBD1A64729BD4D5724F3C1EFC47C6C3D555DA9D2C6AD741EDDC3D893",
    ),
    "Saved/Config/WindowsEditor/EditorPerProjectUserSettings.ini": (
        325842, 1786818627029795900,
        "A49B0A33324C7C4D4E046BEB6599DFE2C1CF0BA4B13254D98640301464C203BC",
    ),
    "Saved/SourceControl/UncontrolledChangelists.json": (
        2595851, 1786818622833182900,
        "074B8B44A924C181357AFB14F645FC3F630A726AB1EC5A1DE04F0CEC28A5A225",
    ),
    "Scripts/__pycache__/cairnwell_2040_panel_modules_v001.cpython-311.pyc": (
        75391, 1786818597650179800,
        "6E927E876856D26736BA2AA2727510A88C4731185FE10EFC915A2E333E6D9D8A",
    ),
}
CRASH_CONFIG_ROOT = PROJECT / "Saved/Config/CrashReportClient"
CRASH_CONFIG_PATTERN = re.compile(
    r"^Saved/Config/CrashReportClient/UECC-Windows-[0-9A-F]{32}/"
    r"CrashReportClient\.ini$"
)
CRASH_CONFIG_BYTES = 239
CRASH_CONFIG_SHA256 = (
    "CE69D7E7BBD1A64729BD4D5724F3C1EFC47C6C3D555DA9D2C6AD741EDDC3D893"
)
TOOL_PATHS = (
    "Scripts/prepare_cairnwell_2040_panel_modules_recovery_v002_contract.py",
    "Scripts/cairnwell_2040_panel_modules_recovery_v002.py",
    "Scripts/validate_cairnwell_2040_panel_modules_recovery_v002.py",
    "Scripts/verify_cairnwell_2040_panel_modules_recovery_v002.py",
    "Scripts/run_cairnwell_2040_panel_modules_recovery_v002.ps1",
    "Scripts/tests/test_cairnwell_2040_panel_modules_recovery_v002.py",
    "Docs/OneFactory/CAIRNWELL_2040_PANEL_MODULES_RECOVERY_V002.md",
)


class ContractError(RuntimeError):
    """Fail-closed recovery contract error."""


def strict_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"duplicate JSON property forbidden: {key!r}")
        result[key] = value
    return result


def strict_json(path: Path, label: str) -> dict:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8-sig"), object_pairs_hook=strict_pairs
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"{label} is unreadable") from exc
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be a JSON object")
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
    except ValueError:
        return str(path.resolve())


def row(path: Path) -> dict:
    if not path.is_file():
        raise ContractError(f"required file absent: {path}")
    stat = path.stat()
    return {
        "path": relative(path),
        "bytes": stat.st_size,
        "sha256": sha256(path),
    }


def exact_row(path: Path) -> dict:
    result = row(path)
    result["mtime_ns"] = path.stat().st_mtime_ns
    return result


def canonical_hash(rows: list[dict]) -> str:
    compact = [
        {key: item[key] for key in ("path", "bytes", "mtime_ns", "sha256")}
        for item in sorted(rows, key=lambda value: value["path"].casefold())
    ]
    return hashlib.sha256(
        json.dumps(compact, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest().upper()


def exact_incidental_surfaces() -> dict:
    rows = [exact_row(PROJECT / path) for path in INCIDENTAL_PATHS]
    by_path = {item["path"]: item for item in rows}
    if set(by_path) != set(INCIDENTAL_INCIDENT_ROWS):
        raise ContractError("exact ten incidental-write path closure drift")
    for path, (size, mtime_ns, digest) in INCIDENTAL_INCIDENT_ROWS.items():
        actual = by_path[path]
        if (
            actual["bytes"] != size
            or actual["mtime_ns"] != mtime_ns
            or actual["sha256"] != digest
        ):
            raise ContractError(f"post-v001 incidental-write evidence drift: {path}")
    return {
        "file_count": 10,
        "inventory_sha256": canonical_hash(rows),
        "files": sorted(rows, key=lambda value: value["path"].casefold()),
        "pre_post_exact_path_byte_hash_invariance_required": True,
        "mtime_only_touches_must_be_explicitly_recorded": True,
    }


def crash_config_tree() -> dict:
    if not CRASH_CONFIG_ROOT.is_dir():
        raise ContractError("CrashReportClient project config root is absent")
    rows = [
        exact_row(path) for path in CRASH_CONFIG_ROOT.rglob("*") if path.is_file()
    ]
    if not rows or any(
        not CRASH_CONFIG_PATTERN.fullmatch(item["path"])
        or item["bytes"] != CRASH_CONFIG_BYTES
        or item["sha256"] != CRASH_CONFIG_SHA256
        for item in rows
    ):
        raise ContractError("CrashReportClient config tree shape/content drift")
    return {
        "file_count": len(rows),
        "inventory_sha256": canonical_hash(rows),
        "files": sorted(rows, key=lambda value: value["path"].casefold()),
    }


def exact_sidecar(payload: Path, sidecar: Path, expected: str, label: str) -> dict:
    if sha256(payload) != expected:
        raise ContractError(f"{label} payload drift")
    tokens = sidecar.read_text(encoding="ascii").strip().split()
    if tokens != [expected, payload.name]:
        raise ContractError(f"{label} sidecar token/name drift")
    return {"payload": row(payload), "sidecar": row(sidecar)}


def import_baseline_tool():
    spec = importlib.util.spec_from_file_location("panel_baseline_v002_recovery", BASELINE_TOOL)
    if spec is None or spec.loader is None:
        raise ContractError("cannot load frozen panel baseline verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def exact_incident() -> tuple[dict, dict]:
    direct = sorted(path.name for path in AUDIT_ROOT.iterdir()) if AUDIT_ROOT.is_dir() else []
    if direct != [INCIDENT_RUN_ID]:
        raise ContractError(f"panel incident chronology drift: {direct}")
    if not INCIDENT_ROOT.is_dir() or RECOVERY_AUDIT_ROOT.exists():
        raise ContractError("incident root absent or Recovery_v002 already consumed")
    files = {path.name: path for path in INCIDENT_ROOT.iterdir() if path.is_file()}
    if set(files) != set(INCIDENT_FILES) or any(path.is_dir() for path in INCIDENT_ROOT.iterdir()):
        raise ContractError("v001 incident must remain the exact five-file closure")
    checked = {}
    for name, expected in INCIDENT_FILES.items():
        actual = row(files[name])
        if actual["bytes"] != expected["bytes"] or actual["sha256"] != expected["sha256"]:
            raise ContractError(f"v001 incident file drift: {name}")
        checked[name] = actual
    failure = strict_json(INCIDENT_ROOT / "import_failure_v001.json", "v001 failure")
    summary = strict_json(INCIDENT_ROOT / "lane_summary_v001.json", "v001 summary")
    if (
        failure.get("status")
        != "FAIL_CLOSED__CAIRNWELL_2040_PANEL_MODULES_V001_IMPORT"
        or failure.get("error") != "'NoneType' object is not iterable"
        or failure.get("process_id") != 34036
        or summary.get("status")
        != "FAIL_CLOSED__CAIRNWELL_2040_PANEL_MODULES_V001_IMPORT_LANE"
        or summary.get("import_process") != {"process_id": 34036, "exit_code": 0}
        or summary.get("validation_process") is not None
        or "CrashReportClientEditor:636" not in str(summary.get("error"))
    ):
        raise ContractError("v001 incident receipt/summary identity drift")
    return checked, failure


def exact_packages(failure: dict) -> dict:
    expected = failure.get("destination_preserved_for_recovery")
    if not isinstance(expected, dict) or len(expected) != 11:
        raise ContractError("v001 failure does not pin exactly 11 package files")
    actual_paths = sorted(path for path in DEST_ROOT.rglob("*") if path.is_file())
    actual = {relative(path): exact_row(path) for path in actual_paths}
    simplified = {
        key: {field: value for field, value in item.items() if field != "path"}
        for key, item in actual.items()
    }
    if simplified != expected or any(path.is_dir() and path.name != "Meshes" for path in DEST_ROOT.rglob("*")):
        raise ContractError("current panel destination differs from exact v001 package closure")
    return simplified


def crash_monitor_evidence() -> dict:
    actual = row(CRASH_MONITOR_LOG)
    if actual["bytes"] != CRASH_MONITOR_LOG_BYTES or actual["sha256"] != CRASH_MONITOR_LOG_SHA256:
        raise ContractError("historical CrashReportClient monitor log drift")
    text = CRASH_MONITOR_LOG.read_text(encoding="utf-8-sig", errors="replace")
    required = (
        "CrashReportClientEditor.exe",
        "-MONITOR=34036",
        "-RespawnedInstance",
        "LogCrashReportClientDiagnostics: App/ExitCode:0",
        "LogCrashReportClientDiagnostics: CRC/Shutdown:",
        "LogExit: Exiting.",
    )
    if any(token not in text for token in required):
        raise ContractError("normal CrashReportClient monitor topology drift")
    recent_crashes = [
        path.name for path in (PROJECT / "Saved/Crashes").iterdir()
        if path.stat().st_mtime_ns >= 1786818300000000000
    ] if (PROJECT / "Saved/Crashes").is_dir() else []
    if recent_crashes:
        raise ContractError(f"unexpected crash directory at/after incident: {recent_crashes}")
    return {
        "log": actual,
        "monitored_editor_process_id": 34036,
        "runner_observed_lingering_process": "CrashReportClientEditor:636",
        "observed_pid_636_binding_to_editor_process_unproven": True,
        "monitor_exit_code": 0,
        "normal_monitor_not_editor_crash": True,
        "saved_crash_directories_at_or_after_incident": [],
    }


def build_payload(deep_baseline_verify: bool = True) -> dict:
    panel_contract = exact_sidecar(
        PANEL_CONTRACT, PANEL_CONTRACT_SHA, PANEL_CONTRACT_SHA256, "panel contract"
    )
    panel_baseline = exact_sidecar(
        PANEL_BASELINE, PANEL_BASELINE_SHA, PANEL_BASELINE_SHA256, "panel baseline v002"
    )
    baseline = strict_json(PANEL_BASELINE, "panel baseline v002")
    if (
        baseline.get("$schema")
        != "lineboss/cairnwell-2040-panel-modules-v001/unreal-import-baseline/v2"
        or baseline.get("status")
        != (
            "FROZEN__CAIRNWELL_2040_PANEL_MODULES_V001_PROJECT_BASELINE_V002__"
            "AFTER_CONCURRENT_AUTHORIZED_PAINT_SOURCE_DRIFT"
        )
    ):
        raise ContractError("panel baseline v002 identity drift")
    if deep_baseline_verify:
        import_baseline_tool().verify_post_import_immutable()
    incident, failure = exact_incident()
    packages = exact_packages(failure)
    incidental = exact_incidental_surfaces()
    crash_configs = crash_config_tree()
    tooling = [row(PROJECT / path) for path in TOOL_PATHS]
    return {
        "$schema": CONTRACT_SCHEMA,
        "status": CONTRACT_STATUS,
        "project_root": str(PROJECT),
        "panel_contract": panel_contract,
        "panel_baseline_v002": panel_baseline,
        "baseline_authority": {
            "source": {
                "file_count": baseline["source"]["file_count"],
                "inventory_sha256": baseline["source"]["inventory_sha256"],
            },
            "protected": {
                "file_count": baseline["protected"]["file_count"],
                "inventory_sha256": baseline["protected"]["inventory_sha256"],
            },
            "lane": {
                "file_count": baseline["lane"]["file_count"],
                "inventory_sha256": baseline["lane"]["inventory_sha256"],
            },
            "runtime": {
                "file_count": baseline["runtime"]["file_count"],
                "inventory_sha256": baseline["runtime"]["inventory_sha256"],
                "package_sha256": baseline["runtime_authority"]["package_sha256"],
            },
            "asset_registry_cache": baseline["asset_registry_cache"],
            "legacy_asset_registry_cache_absence":
                baseline["legacy_asset_registry_cache_absence"],
        },
        "incident_v001": {
            "run_id": INCIDENT_RUN_ID,
            "run_root": relative(INCIDENT_ROOT),
            "files": incident,
            "importer_process_id": 34036,
            "importer_exit_code": 0,
            "validator_launched": False,
            "primary_failure": "OPTIONAL_ASSET_REGISTRY_DEPENDENCY_RESULT_ITERATED_AS_ARRAY",
            "strict_validation_completed": False,
        },
        "normal_crash_monitor_evidence": crash_monitor_evidence(),
        "original_v001_incidental_project_writes": incidental,
        "recovery_preflight_crash_reporter_config_tree": crash_configs,
        "destination": {
            "namespace": (
                "/Game/LineBoss/Factory/OneFactory/v001/Vehicles/"
                "Cairnwell2040PanelModules_v001"
            ),
            "disk_root": relative(DEST_ROOT),
            "package_count": 11,
            "package_files": packages,
            "directory_paths": [relative(DEST_ROOT / "Meshes")],
        },
        "tooling": tooling,
        "recovery": {
            "audit_root": relative(RECOVERY_AUDIT_ROOT),
            "process_count": 1,
            "process_role": "DISTINCT_FRESH_READ_ONLY_PERSISTED_VALIDATOR",
            "dependency_none_allowed_same_process_nonpersisted_only": True,
            "dependency_none_allowed_fresh_persisted_validation": False,
            "persisted_dependency_options": {
                "include_soft_package_references": True,
                "include_hard_package_references": True,
                "include_game_package_references": True,
                "include_editor_only_package_references": False,
                "include_searchable_names": False,
                "include_soft_management_references": False,
                "include_hard_management_references": False,
            },
            "normal_crc_monitor_natural_exit_wait_seconds": 15,
            "normal_crc_monitor_zero_process_stabilization_milliseconds": 1000,
            "normal_crc_monitor_must_bind_completed_editor_pid": True,
            "exact_existing_incidental_files_must_remain_path_byte_hash_exact": True,
            "existing_incidental_mtime_only_touches_must_be_recorded": True,
            "crash_reporter_config_new_file_maximum": 1,
            "crash_reporter_config_new_file_pattern": CRASH_CONFIG_PATTERN.pattern,
            "crash_reporter_config_new_file_bytes": CRASH_CONFIG_BYTES,
            "crash_reporter_config_new_file_sha256": CRASH_CONFIG_SHA256,
            "python_bytecode_write_suppression_environment": {
                "name": "PYTHONDONTWRITEBYTECODE",
                "value": "1",
            },
            "uncontrolled_changelist_write_suppression_override": (
                "-ini:Editor:[/Script/SourceControl.SourceControlPreferences]:"
                "bEnableUncontrolledChangelists=False"
            ),
            "python_stub_write_suppression_override": (
                "-ini:EditorPerProjectUserSettings:"
                "[/Script/PythonScriptPlugin.PythonScriptPluginUserSettings]:"
                "bDeveloperMode=False"
            ),
            "global_config_cache_write_suppression_flag": "-nowrite",
            "required_editor_command_line_tokens": [
                "/Engine/Maps/Entry",
                "-Unattended",
                "-nop4",
                "-NullRHI",
                "-NoCompile",
                "-NoCompileEditor",
                "-NoAutoSave",
                "-NoSaveOnExit",
                "-NoLoadStartupPackages",
                "-NoRestoreOpenAssetTabs",
                "-NoAssetRegistryCacheWrite",
                "-nowrite",
                "-ExecutePythonScript=",
                "-abslog=",
            ],
        },
        "policy": {
            "reimport_authorized": False,
            "content_write_authorized": False,
            "content_move_delete_authorized": False,
            "map_load_save_authorized": False,
            "automatic_cleanup_authorized": False,
            "only_recovery_audit_evidence_writes_authorized": False,
            "recovery_audit_plus_exactly_bounded_engine_ephemera_only": False,
            "authority_surfaces_plus_enumerated_known_ephemera_guarded": True,
            "zero_untracked_non_authority_ephemera_write_claimed": False,
            "existing_incidental_file_content_mutation_authorized": False,
            "existing_incidental_file_mtime_only_touch_authorized": True,
            "at_most_one_new_normal_crc_config_file_authorized": True,
            "source_protected_lane_runtime_cache_must_remain_exact": True,
            "v001_incident_and_packages_must_remain_byte_exact": True,
            "latest_or_fallback_selection_authorized": False,
            "explicit_quit_editor_forbidden": True,
            "python_bytecode_write_suppression_required": True,
            "uncontrolled_changelist_write_suppression_required": True,
            "python_stub_write_suppression_required": True,
            "global_config_cache_write_suppression_required": True,
        },
    }


def create(acknowledgement: str) -> None:
    if acknowledgement != ACK_TOKEN:
        raise ContractError("exact Recovery_v002 freeze acknowledgement missing")
    if OUTPUT.exists() or OUTPUT_SHA.exists():
        raise ContractError("refusing to overwrite Recovery_v002 contract pair")
    payload = build_payload(deep_baseline_verify=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    digest = sha256(OUTPUT)
    OUTPUT_SHA.write_text(f"{digest}  {OUTPUT.name}\n", encoding="ascii")
    print("PASS__CAIRNWELL_2040_PANEL_MODULES_VALIDATION_ONLY_RECOVERY_V002_CONTRACT_FROZEN")
    print(digest)


def verify() -> None:
    if not OUTPUT.is_file() or not OUTPUT_SHA.is_file():
        raise ContractError("Recovery_v002 contract pair is absent")
    digest = sha256(OUTPUT)
    if OUTPUT_SHA.read_text(encoding="ascii").strip().split() != [digest, OUTPUT.name]:
        raise ContractError("Recovery_v002 contract sidecar drift")
    frozen = strict_json(OUTPUT, "Recovery_v002 contract")
    if frozen != build_payload(deep_baseline_verify=True):
        raise ContractError("Recovery_v002 frozen contract no longer reproduces")
    print("PASS__CAIRNWELL_2040_PANEL_MODULES_VALIDATION_ONLY_RECOVERY_V002_CONTRACT_REVERIFIED")
    print(digest)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--acknowledgement", default="")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        verify()
    else:
        create(args.acknowledgement)


if __name__ == "__main__":
    main()
