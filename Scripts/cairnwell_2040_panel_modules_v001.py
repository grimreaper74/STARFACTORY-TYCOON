"""Shared UE 5.8 guards for Cairnwell2040PanelModules_v001.

This module is imported only by the guarded Unreal importer/validator.  It
enforces the frozen offline authorities, immutable separate runtime packages,
mapless Engine Entry bootstrap, exact 11-mesh closure, shared datum/bounds,
authored LODs, one UV/semantic material slot, and collision/Nav/Nanite-off
policy.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
EXPECTED_PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8").resolve()
CONTRACT = PROJECT / "Scripts/cairnwell_2040_panel_modules_v001_import_contract.json"
CONTRACT_SHA = PROJECT / "Scripts/cairnwell_2040_panel_modules_v001_import_contract.sha256"
BASELINE = PROJECT / "Scripts/cairnwell_2040_panel_modules_v001_import_baseline_v002.json"
BASELINE_SHA = PROJECT / "Scripts/cairnwell_2040_panel_modules_v001_import_baseline_v002.sha256"
DEST = (
    "/Game/LineBoss/Factory/OneFactory/v001/Vehicles/"
    "Cairnwell2040PanelModules_v001"
)
DEST_DISK = PROJECT / (
    "Content/LineBoss/Factory/OneFactory/v001/Vehicles/"
    "Cairnwell2040PanelModules_v001"
)
RUNTIME_DEST = (
    "/Game/LineBoss/Factory/OneFactory/v001/Vehicles/"
    "Cairnwell2040Runtime_v001"
)
RUNTIME_AUDIT_ROOT = PROJECT / (
    "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
    "UnrealImportLane_v001"
)
RUNTIME_RECOVERY_V013_AUDIT_ROOT = RUNTIME_AUDIT_ROOT / "Recovery_v013"
EXPECTED_RUNTIME_RECOVERY_V013_RUN_ID = "20260815T172802Z-1389784f"
EXPECTED_RUNTIME_RECOVERY_V013_CONTRACT_SHA256 = (
    "5D2B1929086AD33A8354ED0759509BCC6AFFEF8CD4E5BDE77A54546B53E95F12"
)
EXPECTED_RUNTIME_INCIDENT_CHAIN_SHA256 = (
    "392E5F5D4B3291D69F770B797982BD34D06992A45A78EB5F36CE3C66C257D874"
)
EXPECTED_RUNTIME_V013_RECEIPT_SHA256 = (
    "54A332C47FE71CE975EE666331882369855770C13B81CE6C195488A957127E44"
)
EXPECTED_RUNTIME_V013_SUMMARY_SHA256 = (
    "D24261F1929D3B44EBF6526C148E044A403006DB738F52257A1A16D9CB432488"
)
AUDIT_ROOT = PROJECT / (
    "Saved/Audits/OneFactory/Vehicles/Cairnwell2040PanelModules_v001/"
    "UnrealImportLane_v001"
)
RUN_ROOT_ENV = "LINEBOSS_CAIRNWELL_2040_PANEL_MODULES_V001_RUN_ROOT"
ACK_ENV = "LINEBOSS_CAIRNWELL_2040_PANEL_MODULES_V001_ACK"
ACK_TOKEN = "IMPORT_FROZEN_CAIRNWELL_2040_PANEL_MODULES_V001_ONCE"
INTERCHANGE_FBX_CVAR = "Interchange.FeatureFlags.Import.FBX"
IMPORT_RECEIPT = "import_receipt_v001.json"
IMPORT_FAILURE = "import_failure_v001.json"
VALIDATION_RECEIPT = "fresh_process_validation_receipt_v001.json"
VALIDATION_FAILURE = "fresh_process_validation_failure_v001.json"
SUMMARY = "lane_summary_v001.json"
RESULT_NAMES = {IMPORT_RECEIPT, IMPORT_FAILURE, VALIDATION_RECEIPT, VALIDATION_FAILURE, SUMMARY}
CONTRACT_STATUS = "FROZEN__APPROVED_CAIRNWELL_2040_PANEL_MODULES_V001__READY_FOR_BASELINE"
BASELINE_STATUS = (
    "FROZEN__CAIRNWELL_2040_PANEL_MODULES_V001_PROJECT_BASELINE_V002__"
    "AFTER_CONCURRENT_AUTHORIZED_PAINT_SOURCE_DRIFT"
)
BASELINE_SCHEMA = (
    "lineboss/cairnwell-2040-panel-modules-v001/unreal-import-baseline/v2"
)
FAILED_BASELINE_V001_SHA256 = (
    "6CC7C1F6528A780C486AB8DFEC506066C42298CC516B599BD48B3A94D714FE8F"
)
FAILED_BASELINE_V001_SIDECAR_FILE_SHA256 = (
    "BAAF1653721D564149E73363F08335628A3D45C05F8F5A322435BB3BC6D3E0EB"
)
EXPECTED_MAPLESS_STARTUP_OVERRIDE = (
    "-ini:EditorPerProjectUserSettings:"
    "[/Script/UnrealEd.EditorLoadingSavingSettings]:LoadLevelAtStartup=None"
)
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
SEMANTIC_SLOT = "VehiclePanelSurface"
library = unreal.EditorAssetLibrary


def fail(message: str) -> None:
    raise RuntimeError("CAIRNWELL_2040_PANEL_MODULES_V001_LANE_FAIL: " + message)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT).as_posix()
    except ValueError as exc:
        fail(f"path escapes exact project: {path}")
        raise exc


def file_row(path: Path) -> dict:
    if not path.is_file():
        fail("required file missing: " + str(path))
    stat = path.stat()
    return {
        "path": relative(path),
        "bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": sha256(path),
    }


def canonical_hash(rows: list[dict]) -> str:
    compact = [
        {key: item[key] for key in ("path", "bytes", "mtime_ns", "sha256")}
        for item in sorted(rows, key=lambda value: value["path"].casefold())
    ]
    return hashlib.sha256(
        json.dumps(compact, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest().upper()


def strict_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            fail(f"duplicate raw JSON property forbidden: {key!r}")
        result[key] = value
    return result


def strict_json(path: Path, label: str) -> dict:
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8-sig"), object_pairs_hook=strict_pairs
        )
    except (OSError, json.JSONDecodeError) as exc:
        fail(label + " JSON is unreadable: " + str(exc))
    if not isinstance(payload, dict):
        fail(label + " must be a JSON object")
    return payload


def sidecar_hash(payload: Path, sidecar: Path, label: str) -> str:
    if not payload.is_file() or not sidecar.is_file():
        fail(f"{label} and SHA-256 sidecar are absent")
    digest = sha256(payload)
    if sidecar.read_text(encoding="ascii").strip().split()[0].upper() != digest:
        fail(f"{label} SHA-256 sidecar mismatch")
    return digest


def run_root() -> Path:
    raw = os.environ.get(RUN_ROOT_ENV, "").strip()
    if not raw or os.environ.get(ACK_ENV, "").strip() != ACK_TOKEN:
        fail("guarded runner environment/acknowledgement absent")
    root = Path(raw).resolve()
    if root == AUDIT_ROOT.resolve() or not inside(root, AUDIT_ROOT) or not root.is_dir():
        fail("run root escapes or is absent: " + str(root))
    return root


def require_engine_entry_bootstrap_world() -> str:
    command_line = str(unreal.SystemLibrary.get_command_line())
    if EXPECTED_MAPLESS_STARTUP_OVERRIDE not in command_line:
        fail("exact transient LoadLevelAtStartup=None override is absent")
    if command_line.count("-NoAssetRegistryCacheWrite") != 1:
        fail("exactly one -NoAssetRegistryCacheWrite command-line guard is required")
    if os.environ.get("UE_SKIP_UBT_SDK_SETUP") != "1":
        fail("UE_SKIP_UBT_SDK_SETUP=1 startup guard is absent")
    subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = subsystem.get_editor_world() if subsystem else None
    path = world.get_path_name() if world else ""
    if path != "/Engine/Maps/Entry.Entry":
        fail("panel lane must bootstrap only /Engine/Maps/Entry.Entry; actual=" + path)
    return path


def verify_plain_row(expected: dict, label: str) -> dict:
    actual = file_row(PROJECT / expected.get("path", ""))
    if any(actual[key] != expected.get(key) for key in ("path", "bytes", "sha256")):
        fail(label + " file authority drift")
    return actual


def verify_runtime_authority(runtime: dict) -> dict:
    if (
        runtime.get("destination_namespace") != RUNTIME_DEST
        or runtime.get("persisted_dependency_closure_verified") is not True
        or runtime.get("all_package_hashes_unchanged") is not True
        or runtime.get("cache_and_legacy_surfaces_unchanged") is not True
        or runtime.get("no_build_tool_invoked") is not True
        or set(runtime.get("materials", {}))
        != {"biw_galvanised", "ed_coat", "player_paint"}
        or runtime.get("recovery_v013_contract_sha256")
        != EXPECTED_RUNTIME_RECOVERY_V013_CONTRACT_SHA256
        or runtime.get("incident_chain_sha256")
        != EXPECTED_RUNTIME_INCIDENT_CHAIN_SHA256
        or runtime.get("recovery_v013_run_id")
        != EXPECTED_RUNTIME_RECOVERY_V013_RUN_ID
        or runtime.get("vehicle_model_id") != "CAIRNWELL_2040"
        or runtime.get("production_recipe_id")
        != "CAIRNWELL_2040_DEVELOPMENT_RECIPE_V001"
        or runtime.get("current_geometry_authority_id")
        != "Cairnwell2040Runtime_v001_V009ImportedGeometry"
        or runtime.get("lifecycle")
        != "DEVELOPMENT__APPROVED_FOR_GAME_BUILD__NOT_FINAL_ART"
        or runtime.get("final_release_visual_lock_claimed") is not False
        or runtime.get("geometry_revisionable") is not True
    ):
        fail("approved runtime V013/material/development-model identity drift")
    evidence_keys = (
        "contract", "contract_sidecar", "baseline", "baseline_sidecar",
        "recovery_v013_contract", "recovery_v013_contract_sidecar",
        "fresh_validation_receipt", "lane_summary",
    )
    evidence = {
        key: verify_plain_row(runtime[key], "runtime " + key)
        for key in evidence_keys
    }
    if (
        evidence["contract"]["sha256"] != runtime.get("contract_sha256")
        or evidence["baseline"]["sha256"] != runtime.get("baseline_sha256")
        or evidence["recovery_v013_contract"]["sha256"]
        != EXPECTED_RUNTIME_RECOVERY_V013_CONTRACT_SHA256
        or evidence["fresh_validation_receipt"]["sha256"]
        != EXPECTED_RUNTIME_V013_RECEIPT_SHA256
        or evidence["lane_summary"]["sha256"]
        != EXPECTED_RUNTIME_V013_SUMMARY_SHA256
    ):
        fail("runtime V013 evidence digest seam drift")
    for sidecar_key, digest_key in (
        ("contract_sidecar", "contract_sha256"),
        ("baseline_sidecar", "baseline_sha256"),
        ("recovery_v013_contract_sidecar", "recovery_v013_contract_sha256"),
    ):
        sidecar_path = PROJECT / runtime[sidecar_key]["path"]
        if (
            sidecar_path.read_text(encoding="ascii").strip().split()[0].upper()
            != runtime[digest_key]
        ):
            fail("runtime sidecar content drift: " + sidecar_key)

    run_root = (PROJECT / str(runtime.get("recovery_v013_run_root", ""))).resolve()
    expected_root = (
        RUNTIME_RECOVERY_V013_AUDIT_ROOT / EXPECTED_RUNTIME_RECOVERY_V013_RUN_ID
    ).resolve()
    parent_roots = (
        [path.resolve() for path in RUNTIME_RECOVERY_V013_AUDIT_ROOT.iterdir()
         if path.is_dir()]
        if RUNTIME_RECOVERY_V013_AUDIT_ROOT.is_dir() else []
    )
    files = runtime.get("recovery_v013_result_files")
    if (
        run_root != expected_root
        or parent_roots != [expected_root]
        or any(path.is_file() for path in RUNTIME_RECOVERY_V013_AUDIT_ROOT.iterdir())
        or not isinstance(files, dict)
        or len(files) != 5
        or {path.name for path in run_root.iterdir() if path.is_file()} != set(files)
        or any(path.is_dir() for path in run_root.iterdir())
    ):
        fail("runtime authority no longer has exact V013 five-file run topology")
    checked_files = {
        name: verify_plain_row(spec, "runtime V013 result " + name)
        for name, spec in files.items()
    }
    if any((PROJECT / spec["path"]).resolve().parent != run_root for spec in files.values()):
        fail("runtime V013 result evidence escaped exact run root")

    receipt_path = PROJECT / runtime["fresh_validation_receipt"]["path"]
    summary_path = PROJECT / runtime["lane_summary"]["path"]
    receipt = strict_json(receipt_path, "runtime V013 validation receipt")
    summary = strict_json(summary_path, "runtime V013 lane summary")
    packages = runtime.get("package_sha256")
    cache = runtime.get("asset_registry_cache")
    legacy = runtime.get("legacy_asset_registry_cache_absence")
    if (
        receipt.get("$schema")
        != "lineboss/audit/cairnwell-2040-runtime-v001/recovery-v013/fresh-process-validation/v13"
        or receipt.get("status")
        != "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V013_DISTINCT_FRESH_PROCESS__READ_ONLY_RELOAD_OF_V009_PASS_IMPORT__EXACT_PERSISTED_DEPENDENCIES__ZERO_CACHE_DELETION_OR_WRITE__11_PACKAGE_HASHES_UNCHANGED"
        or summary.get("$schema")
        != "lineboss/audit/cairnwell-2040-runtime-v001/recovery-v013/validation-only-lane-summary/v13"
        or summary.get("status")
        != "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V013_GUARDED_VALIDATION_ONLY_OF_V009_PASS_IMPORT"
        or receipt.get("recovery_contract_sha256")
        != EXPECTED_RUNTIME_RECOVERY_V013_CONTRACT_SHA256
        or summary.get("recovery_contract_sha256")
        != EXPECTED_RUNTIME_RECOVERY_V013_CONTRACT_SHA256
        or receipt.get("incident_chain_sha256")
        != EXPECTED_RUNTIME_INCIDENT_CHAIN_SHA256
        or receipt.get("package_sha256_before_loads") != packages
        or receipt.get("package_sha256_after_loads") != packages
        or summary.get("post_exit_package_sha256") != packages
        or receipt.get("asset_registry_cache_before") != cache
        or receipt.get("asset_registry_cache_after") != cache
        or summary.get("post_exit_asset_registry_cache") != cache
        or receipt.get("legacy_asset_registry_cache_absence_before") != legacy
        or receipt.get("legacy_asset_registry_cache_absence_after") != legacy
        or summary.get("post_exit_legacy_asset_registry_cache_absence") != legacy
        or receipt.get("persisted_asset_registry_dependency_closure_verified") is not True
        or receipt.get("all_package_hashes_unchanged") is not True
        or receipt.get("no_asset_registry_cache_write_command_line_verified") is not True
        or receipt.get("asset_mutation_count") != 0
        or receipt.get("import_or_reimport_process_count") != 0
        or summary.get("validation_process", {}).get("exit_code") != 0
        or summary.get("validation_process", {}).get(
            "fatal_or_build_tool_log_patterns") != []
        or summary.get("no_build_tool_invoked") is not True
        or summary.get("exact_ubt_command_line_matches") != 0
        or summary.get("environment_restoration_verified") is not True
        or summary.get("error") is not None
    ):
        fail("runtime V013 receipt/package/cache/clean-exit closure drift")
    package_rows = {}
    for package, expected_hash in packages.items():
        disk = PROJECT / ("Content/" + package.removeprefix("/Game/") + ".uasset")
        actual_hash = sha256(disk)
        if actual_hash != expected_hash:
            fail("runtime package hash drift: " + package)
        package_rows[package] = actual_hash
    if len(package_rows) != 11:
        fail("runtime package closure is not exactly 11")
    return {
        "evidence": evidence,
        "v013_result_evidence": checked_files,
        "package_sha256": package_rows,
        "asset_registry_cache": cache,
        "legacy_asset_registry_cache_absence": legacy,
    }


def load_contract() -> tuple[dict, str]:
    digest = sidecar_hash(CONTRACT, CONTRACT_SHA, "approved panel import contract")
    payload = strict_json(CONTRACT, "panel import contract")
    destination = payload.get("destination", {})
    materials = payload.get("material_reuse", {})
    provenance = payload.get("provenance", {})
    runtime = payload.get("runtime_authority", {})
    authority_boundary = payload.get("project_authority_boundary", {})
    policy = payload.get("policy", {})
    if (
        payload.get("$schema")
        != "lineboss/cairnwell-2040-panel-modules-v001/unreal-import-contract/v1"
        or payload.get("status") != CONTRACT_STATUS
        or destination.get("namespace") != DEST
        or int(destination.get("expected_mesh_count", -1)) != 11
        or int(destination.get("expected_authored_lod_count", -1)) != 33
        or int(destination.get("expected_texture_count", -1)) != 0
        or int(destination.get("expected_material_count", -1)) != 0
        or int(destination.get("expected_package_count", -1)) != 11
        or int(destination.get("expected_source_fbx_count", -1)) != 33
        or set(payload.get("modules", {})) != set(PANEL_IDS)
        or provenance.get("source_authority_version") != "v002"
        or provenance.get("unreal_destination_version") != "v001"
        or provenance.get("geometry_method") != "PARAMETRIC_NATIVE_AUTHORING"
        or provenance.get("manifest", {}).get("sha256")
        != "2FF38357BEC9FB890B2DCCCBC4C5E1728AB35D5BCB772F08811522540F6DF6E8"
        or provenance.get("production_audit", {}).get("sha256")
        != "F7C9CF062DBC1E5A4B5CBFE8B71A9BD79E1536D0523802F8F118562E9CC24762"
        or provenance.get("freeze_receipt", {}).get("sha256")
        != "B31900FE90D237952E788361309B747B8C7D831536034CBD23894408E0925B3D"
        or int(provenance.get("frozen_v002_file_count", -1)) != 110
        or len(provenance.get("source_files", [])) != 111
        or materials.get("semantic_slot") != SEMANTIC_SLOT
        or materials.get("default_role") != "player_paint"
        or int(materials.get("new_texture_count", -1)) != 0
        or int(materials.get("new_material_count", -1)) != 0
        or payload.get("import_contract", {}).get("editor_bootstrap_world")
        != "/Engine/Maps/Entry.Entry"
        or payload.get("import_contract", {}).get("editor_startup_map_override")
        != EXPECTED_MAPLESS_STARTUP_OVERRIDE
        or payload.get("import_contract", {}).get("project_map_load_save_authorized") is not False
        or runtime.get("recovery_v013_contract_sha256")
        != EXPECTED_RUNTIME_RECOVERY_V013_CONTRACT_SHA256
        or runtime.get("incident_chain_sha256") != EXPECTED_RUNTIME_INCIDENT_CHAIN_SHA256
        or runtime.get(
            "historical_v013_project_snapshots_are_receipt_evidence_not_live_baseline"
        ) is not True
        or runtime.get("current_project_authority_is_the_new_panel_baseline") is not True
        or authority_boundary.get("runtime_v013_project_snapshots_role")
        != "HISTORICAL_VALIDATION_EVIDENCE_ONLY"
        or authority_boundary.get("current_project_authority")
        != "NEW_PANEL_BASELINE_FULL_PROJECT_SNAPSHOT"
        or authority_boundary.get("authorized_intervening_source_evolution")
        != "PAINT_PRESENTATION_SOURCE_EVOLUTION"
        or authority_boundary.get(
            "authorized_intervening_source_evolution_is_not_future_drift_permission"
        ) is not True
        or authority_boundary.get("unrelated_future_drift_authorized") is not False
        or payload.get("import_contract", {}).get(
            "no_asset_registry_cache_write_command_line_flag"
        ) != "-NoAssetRegistryCacheWrite"
        or payload.get("import_contract", {}).get(
            "ubt_startup_guard_environment"
        ) != {"name": "UE_SKIP_UBT_SDK_SETUP", "required_value": "1"}
        or payload.get("import_contract", {}).get(
            "explicit_quit_editor_forbidden"
        ) is not True
        or policy.get("overwrite_reimport_delete_authorized") is not False
        or policy.get("runtime_authority_mutation_authorized") is not False
        or policy.get(
            "post_v013_authorized_source_evolution_must_be_frozen_by_panel_baseline"
        ) is not True
        or policy.get(
            "historical_v013_project_snapshot_may_not_replace_current_panel_baseline"
        ) is not True
        or policy.get("unrelated_post_panel_baseline_drift_authorized") is not False
    ):
        fail("panel contract identity/count/datum/material/safety drift")
    shared = payload.get("shared_datum", {})
    if (
        shared.get("forward_axis") != "+X"
        or shared.get("right_axis") != "+Y"
        or shared.get("up_axis") != "+Z"
        or shared.get("pivot_cm") != [0.0, 0.0, 0.0]
        or shared.get("canonical_dimensions_cm") != [456.0, 188.0, 156.0]
        or shared.get("tyre_contact_z_cm") != 0.0
        or shared.get("car_envelope_min_cm") != [-228.0, -94.0, 0.0]
        or shared.get("car_envelope_max_cm") != [228.0, 94.0, 156.0]
    ):
        fail("full-car shared zero datum/envelope contract drift")
    expected_packages = [payload["modules"][panel_id]["package_path"] for panel_id in PANEL_IDS]
    if expected_packages != destination.get("expected_package_paths") or len(set(expected_packages)) != 11:
        fail("exact 11-package order/path closure drift")
    for panel_id in PANEL_IDS:
        spec = payload["modules"][panel_id]
        lods = spec.get("lods", [])
        if (
            spec.get("material_slots") != [SEMANTIC_SLOT]
            or spec.get("source_authority_version") != "v002"
            or spec.get("unreal_destination_version") != "v001"
            or spec.get("source_material_role") != "player_paint"
            or spec.get("shared_origin_preserved") is not True
            or [item.get("lod") for item in lods] != [0, 1, 2]
            or [item.get("triangles") for item in lods] != spec.get("triangle_chain")
            or not lods[0]["triangles"] > lods[1]["triangles"] > lods[2]["triangles"] > 0
            or any(item.get("uv_channels") != 1 for item in lods)
            or any(item.get("degenerate_triangles") != 0 for item in lods)
            or any(item.get("duplicate_triangles") != 0 for item in lods)
            or any(item.get("zero_length_edges") != 0 for item in lods)
            or any(item.get("boundary_edges") != 0 for item in lods)
            or any(item.get("nonmanifold_edges") != 0 for item in lods)
            or any(item.get("self_intersection_pairs") != 0 for item in lods)
            or any(set(item.get("roundtrip", {})) != {"fbx", "glb"} for item in lods)
            or any(item.get("expected_unreal_bounds", {}).get("pivot_cm") != [0.0, 0.0, 0.0] for item in lods)
            or spec.get("nanite_enabled") is not False
            or spec.get("has_navigation_data") is not False
            or spec.get("collision", {}).get("simple_count") != 0
            or spec.get("collision", {}).get("convex_count") != 0
        ):
            fail("frozen panel geometry/LOD/slot/datum policy drift: " + panel_id)
    for expected in payload.get("provenance", {}).get("source_files", []):
        verify_plain_row(expected, "panel source")
    verify_runtime_authority(payload["runtime_authority"])
    return payload, digest


def load_baseline() -> dict:
    if PROJECT != EXPECTED_PROJECT or str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory":
        fail("running project identity drift")
    contract, contract_digest = load_contract()
    baseline_digest = sidecar_hash(BASELINE, BASELINE_SHA, "panel project baseline")
    payload = strict_json(BASELINE, "panel import baseline")
    if (
        payload.get("$schema")
        != BASELINE_SCHEMA
        or payload.get("status") != BASELINE_STATUS
        or payload.get("superseded_failed_baseline_v001", {}).get("status")
        != (
            "PRESERVED__UNSELECTABLE__FAILED_IMMEDIATE_REVERIFICATION__"
            "CONCURRENT_AUTHORIZED_PAINT_SOURCE_DRIFT"
        )
        or payload.get("superseded_failed_baseline_v001", {}).get(
            "baseline", {}
        ).get("sha256") != FAILED_BASELINE_V001_SHA256
        or payload.get("superseded_failed_baseline_v001", {}).get(
            "sidecar", {}
        ).get("sha256") != FAILED_BASELINE_V001_SIDECAR_FILE_SHA256
        or payload.get("superseded_failed_baseline_v001", {}).get(
            "may_authorize_unreal"
        ) is not False
        or payload.get("superseded_failed_baseline_v001", {}).get(
            "may_be_selected_as_current_baseline"
        ) is not False
        or payload.get("contract", {}).get("sha256") != contract_digest
        or payload.get("destination") != contract.get("destination")
        or payload.get("shared_datum") != contract.get("shared_datum")
        or payload.get("runtime_authority") != contract.get("runtime_authority")
        or payload.get("project_authority_boundary", {}).get(
            "runtime_v013_project_snapshots_role"
        ) != "HISTORICAL_VALIDATION_EVIDENCE_ONLY"
        or payload.get("project_authority_boundary", {}).get(
            "historical_runtime_v013", {}
        ) != {
            "source": contract["runtime_authority"]["historical_v013_source_snapshot"],
            "protected": contract["runtime_authority"][
                "historical_v013_protected_snapshot"
            ],
            "prepared_lane": contract["runtime_authority"][
                "historical_v013_prepared_lane_snapshot"
            ],
        }
        or payload.get("project_authority_boundary", {}).get(
            "current_project_authority"
        ) != "THIS_PANEL_BASELINE_FULL_PROJECT_SNAPSHOT"
        or payload.get("project_authority_boundary", {}).get(
            "authorized_intervening_source_evolution"
        ) != "PAINT_PRESENTATION_SOURCE_EVOLUTION"
        or payload.get("project_authority_boundary", {}).get(
            "authorized_intervening_source_evolution_is_now_frozen"
        ) is not True
        or payload.get("project_authority_boundary", {}).get(
            "unrelated_future_drift_authorized"
        ) is not False
        or payload.get("material_reuse") != contract.get("material_reuse")
        or payload.get("modules") != contract.get("modules")
        or payload.get("import_contract") != contract.get("import_contract")
        or payload.get("policy") != contract.get("policy")
    ):
        fail("frozen panel baseline identity/contract drift")
    payload["_contract_sha256"] = contract_digest
    payload["_baseline_sha256"] = baseline_digest
    return payload


def verify_inventory(snapshot: dict, label: str) -> dict:
    rows = []
    for expected in snapshot["files"]:
        actual = file_row(PROJECT / expected["path"])
        if any(actual[key] != expected[key] for key in ("path", "bytes", "mtime_ns", "sha256")):
            fail(f"{label} file drift: {expected['path']}")
        rows.append(actual)
    digest = canonical_hash(rows)
    if len(rows) != int(snapshot["file_count"]) or digest != snapshot["inventory_sha256"]:
        fail(label + " inventory drift")
    return {"file_count": len(rows), "inventory_sha256": digest}


def verify_source(baseline: dict) -> dict:
    return verify_inventory(baseline["source"], "approved panel source")


def verify_runtime(baseline: dict) -> dict:
    inventory = verify_inventory(baseline["runtime"], "approved runtime authority")
    authority = verify_runtime_authority(baseline["runtime_authority"])
    return {**inventory, "package_sha256": authority["package_sha256"]}


def verify_protected(baseline: dict) -> dict:
    protected = baseline["protected"]
    union = set()
    for group in protected["groups"]:
        selected = {PROJECT / rel for rel in group.get("files", [])}
        for root_relative in group.get("roots", []):
            root = PROJECT / root_relative
            if not root.is_dir():
                if group.get("allow_empty"):
                    continue
                fail("protected root missing: " + root_relative)
            selected.update(path for path in root.rglob("*") if path.is_file())
        exclusions = [PROJECT / rel for rel in group.get("excludes", [])]
        selected = {
            path for path in selected
            if not any(path.resolve() == excluded.resolve() or inside(path, excluded) for excluded in exclusions)
        }
        paths = {relative(path) for path in selected}
        if paths != set(group["paths"]):
            fail("protected group path inventory drift: " + group["name"])
        union.update(paths)
    if union != {item["path"] for item in protected["files"]}:
        fail("protected group union drift")
    return verify_inventory(protected, "protected project")


def verify_lane(baseline: dict) -> dict:
    return verify_inventory(baseline["lane"], "prepared panel lane")


def asset_registry_cache_snapshot() -> dict:
    root = PROJECT / "Intermediate/CachedAssetRegistry"
    if not root.is_dir():
        fail("Intermediate/CachedAssetRegistry is absent")
    rows = [
        file_row(path) for path in sorted(
            (item for item in root.rglob("*") if item.is_file()),
            key=lambda item: str(item).casefold(),
        )
    ]
    result = {
        "root": relative(root),
        "file_count": len(rows),
        "inventory_sha256": canonical_hash(rows),
        "files": rows,
    }
    if result["file_count"] != 2:
        fail("asset-registry cache is not the exact two-file V013 surface")
    return result


def legacy_asset_registry_cache_absence() -> dict:
    root = PROJECT / "Intermediate"
    direct = [path for path in root.iterdir() if path.is_file()] if root.is_dir() else []
    monolithic = [
        path for path in direct if path.name.casefold() == "cachedassetregistry.bin"
    ]
    shards = sorted(
        (
            path for path in direct
            if path.name.casefold().startswith("cachedassetregistry_")
            and path.name.casefold().endswith(".bin")
        ),
        key=lambda path: path.name.casefold(),
    )
    result = {
        "root": "Intermediate",
        "monolithic_path": "Intermediate/CachedAssetRegistry.bin",
        "monolithic_absent": not monolithic,
        "legacy_shard_pattern": "Intermediate/CachedAssetRegistry_*.bin",
        "legacy_shard_paths": [relative(path) for path in shards],
        "matching_path_count": len(shards),
        "windows_case_insensitive_name_match": True,
    }
    if not result["monolithic_absent"] or result["matching_path_count"] != 0:
        fail("legacy asset-registry cache deletion surface is present")
    return result


def namespace_inventory() -> dict:
    if not DEST_DISK.is_dir():
        return {}
    return {
        item["path"]: {key: item[key] for key in ("bytes", "mtime_ns", "sha256")}
        for item in (
            file_row(path) for path in sorted(DEST_DISK.rglob("*"), key=lambda value: str(value).casefold())
            if path.is_file()
        )
    }


def package_hashes(baseline: dict) -> dict[str, str]:
    expected = baseline["destination"]["expected_package_paths"]
    answer = {}
    for package in expected:
        disk = PROJECT / ("Content/" + package.removeprefix("/Game/") + ".uasset")
        if not disk.is_file():
            fail("expected panel package missing: " + package)
        answer[package] = sha256(disk)
    actual = sorted(DEST_DISK.rglob("*.uasset"), key=lambda path: str(path).casefold())
    actual_packages = {
        "/Game/" + path.relative_to(PROJECT / "Content").with_suffix("").as_posix()
        for path in actual
    }
    if len(actual) != 11 or actual_packages != set(expected):
        fail("panel destination package closure is not exact 11")
    return answer


def prior_results() -> list[str]:
    if not AUDIT_ROOT.is_dir():
        return []
    return sorted(
        relative(path) for path in AUDIT_ROOT.rglob("*")
        if path.is_file() and path.name in RESULT_NAMES
    )


def vector(value) -> list[float]:
    return [float(value.x), float(value.y), float(value.z)]


def lod_bounds(mesh, lod_index: int) -> dict:
    dynamic = unreal.DynamicMesh()
    options = unreal.GeometryScriptCopyMeshFromAssetOptions()
    request = unreal.GeometryScriptMeshReadLOD()
    request.set_editor_properties({
        "lod_type": unreal.GeometryScriptLODType.SOURCE_MODEL,
        "lod_index": lod_index,
    })
    dynamic, outcome = unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(
        mesh, dynamic, options, request, False
    )
    if outcome != unreal.GeometryScriptOutcomePins.SUCCESS:
        fail(f"source LOD bounds extraction failed: {mesh.get_name()}:LOD{lod_index}")
    box = dynamic.get_mesh_bounding_box()
    minimum, maximum = vector(box.min), vector(box.max)
    return {
        "minimum_cm": minimum,
        "maximum_cm": maximum,
        "dimensions_cm": [maximum[index] - minimum[index] for index in range(3)],
        "pivot_cm": [0.0, 0.0, 0.0],
    }


def assert_bounds(actual: dict, expected: dict, tolerance: float, label: str) -> None:
    for field in ("minimum_cm", "maximum_cm", "dimensions_cm", "pivot_cm"):
        if max(abs(float(actual[field][index]) - float(expected[field][index])) for index in range(3)) > tolerance:
            fail(f"{label} fitted bounds/shared-origin drift: {field}")


def slot_names(mesh) -> list[str]:
    return [
        str(item.get_editor_property("material_slot_name"))
        for item in mesh.get_editor_property("static_materials")
    ]


def section_slots(mesh, subsystem, lod_index: int, slots: list[str]) -> list[str]:
    output = []
    for section in range(int(mesh.get_num_sections(lod_index))):
        index = int(subsystem.get_lod_material_slot(mesh, lod_index, section))
        if index < 0 or index >= len(slots):
            fail(f"section/material index invalid: {mesh.get_name()}:LOD{lod_index}")
        output.append(slots[index])
    return output


def legacy_import_data(mesh) -> dict:
    data = mesh.get_editor_property("asset_import_data")
    output = {
        "import_uniform_scale": float(data.get_editor_property("import_uniform_scale")),
        "convert_scene": bool(data.get_editor_property("convert_scene")),
        "convert_scene_unit": bool(data.get_editor_property("convert_scene_unit")),
        "force_front_x_axis": bool(data.get_editor_property("force_front_x_axis")),
        "transform_vertex_to_absolute": bool(data.get_editor_property("transform_vertex_to_absolute")),
        "bake_pivot_in_vertex": bool(data.get_editor_property("bake_pivot_in_vertex")),
        "generate_lightmap_u_vs": bool(data.get_editor_property("generate_lightmap_u_vs")),
        "auto_generate_collision": bool(data.get_editor_property("auto_generate_collision")),
        "remove_degenerates": bool(data.get_editor_property("remove_degenerates")),
    }
    expected = {
        "import_uniform_scale": 1.0,
        "convert_scene": True,
        "convert_scene_unit": True,
        "force_front_x_axis": False,
        "transform_vertex_to_absolute": True,
        "bake_pivot_in_vertex": False,
        "generate_lightmap_u_vs": False,
        "auto_generate_collision": False,
        "remove_degenerates": False,
    }
    if output != expected:
        fail("legacy FBX import setting drift: " + mesh.get_name())
    return output


def project_dependencies(package: str) -> set[str]:
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    options = unreal.AssetRegistryDependencyOptions(
        include_soft_package_references=True,
        include_hard_package_references=True,
        include_searchable_names=False,
        include_soft_management_references=False,
        include_hard_management_references=False,
    )
    return {str(value) for value in registry.get_dependencies(package, options)}


def validate_runtime_materials(baseline: dict) -> dict:
    answer = {}
    for role, spec in baseline["material_reuse"]["materials"].items():
        material = library.load_asset(spec["object_path"])
        if not isinstance(material, unreal.MaterialInterface) or material.get_path_name() != spec["object_path"]:
            fail("approved runtime material cannot be loaded: " + role)
        answer[role] = {
            "object_path": material.get_path_name(),
            "package_sha256": baseline["runtime_authority"]["package_sha256"][spec["package_path"]],
        }
    return answer


def validate_mesh(panel_id: str, spec: dict, baseline: dict, subsystem,
                  require_persisted_dependencies: bool) -> dict:
    mesh = library.load_asset(spec["package_path"])
    if not isinstance(mesh, unreal.StaticMesh) or mesh.get_path_name() != spec["object_path"]:
        fail("StaticMesh/object identity drift: " + panel_id)
    if int(mesh.get_num_lods()) != 3:
        fail("authored LOD count drift: " + panel_id)
    screens = [round(float(value), 6) for value in subsystem.get_lod_screen_sizes(mesh)]
    expected_screens = baseline["import_contract"]["lod_screen_sizes"]
    if screens != expected_screens or mesh.is_lod_screen_size_auto_computed():
        fail("manual LOD screen-size drift: " + panel_id)
    slots = slot_names(mesh)
    if slots != [SEMANTIC_SLOT]:
        fail("one semantic panel slot drift: " + panel_id + repr(slots))
    material = mesh.get_material(0)
    bound = material.get_path_name() if material else None
    expected_material = spec["material_bindings"]["default"]
    if bound != expected_material:
        fail("default solid-colour player-paint runtime material binding drift: " + panel_id)
    lod_rows = []
    for lod_index, expected in enumerate(spec["lods"]):
        triangles = int(mesh.get_num_triangles(lod_index))
        vertices = int(mesh.get_num_vertices(lod_index))
        uv_channels = int(mesh.get_num_tex_coords(lod_index))
        bounds = lod_bounds(mesh, lod_index)
        if triangles != int(expected["triangles"]) or vertices <= 0 or uv_channels != 1:
            fail(f"triangle/positive-vertex/exact-one-UV drift: {panel_id}:LOD{lod_index}")
        assert_bounds(
            bounds,
            expected["expected_unreal_bounds"],
            float(baseline["import_contract"]["bounds_tolerance_cm"]),
            f"{panel_id}:LOD{lod_index}",
        )
        sections = section_slots(mesh, subsystem, lod_index, slots)
        if not sections or any(slot != SEMANTIC_SLOT for slot in sections):
            fail(f"LOD section escaped one semantic slot: {panel_id}:LOD{lod_index}")
        lod_rows.append({
            "lod": lod_index,
            "triangles": triangles,
            "vertices": vertices,
            "source_vertices": int(expected["source_vertices"]),
            "uv_channels": uv_channels,
            "source_degenerate_triangles": int(expected["degenerate_triangles"]),
            "source_zero_length_edges": int(expected["zero_length_edges"]),
            "bounds": bounds,
            "section_material_slots": sections,
        })
    chain = [item["triangles"] for item in lod_rows]
    if chain != spec["triangle_chain"] or not chain[0] > chain[1] > chain[2] > 0:
        fail("strict authored LOD triangle chain drift: " + panel_id)
    simple = int(unreal.EditorStaticMeshLibrary.get_simple_collision_count(mesh))
    convex = int(unreal.EditorStaticMeshLibrary.get_convex_collision_count(mesh))
    body = mesh.get_editor_property("body_setup")
    trace_enum = body.get_editor_property("collision_trace_flag") if body else None
    trace = str(trace_enum) if trace_enum is not None else "NONE"
    nanite = bool(subsystem.get_nanite_settings(mesh).get_editor_property("enabled"))
    navigation = bool(mesh.get_editor_property("has_navigation_data"))
    if (
        simple != 0
        or convex != 0
        or trace_enum != unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX
        or nanite
        or navigation
    ):
        fail("collision/Nav/Nanite policy drift: " + panel_id)
    relevant = {
        path for path in project_dependencies(spec["package_path"])
        if path.startswith(DEST + "/") or path.startswith(RUNTIME_DEST + "/")
    }
    expected_dependencies = {expected_material.split(".", 1)[0]}
    if require_persisted_dependencies and relevant != expected_dependencies:
        fail(f"persisted runtime-material dependency drift: {panel_id}:{relevant}")
    return {
        "panel_id": panel_id,
        "object_path": mesh.get_path_name(),
        "lod_count": 3,
        "lod_screen_sizes": screens,
        "lod_screen_size_auto_computed": False,
        "lods": lod_rows,
        "triangle_chain": chain,
        "strict_monotonic_triangles": True,
        "material_slots": slots,
        "bound_material": bound,
        "available_stage_materials": spec["material_bindings"]["available_stage_roles"],
        "simple_collision_count": simple,
        "convex_collision_count": convex,
        "collision_trace_flag": trace,
        "nanite_enabled": nanite,
        "has_navigation_data": navigation,
        "legacy_import_data": legacy_import_data(mesh),
        "persisted_relevant_dependencies": sorted(relevant, key=str.casefold),
        "persisted_dependency_check_required": require_persisted_dependencies,
    }


def validate_all_assets(baseline: dict, require_persisted_dependencies: bool) -> dict:
    subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    if subsystem is None:
        fail("UE 5.8 StaticMeshEditorSubsystem unavailable")
    runtime_before = verify_runtime_authority(baseline["runtime_authority"])["package_sha256"]
    runtime_materials = validate_runtime_materials(baseline)
    meshes = {
        panel_id: validate_mesh(
            panel_id,
            baseline["modules"][panel_id],
            baseline,
            subsystem,
            require_persisted_dependencies,
        )
        for panel_id in PANEL_IDS
    }
    runtime_after = verify_runtime_authority(baseline["runtime_authority"])["package_sha256"]
    if runtime_after != runtime_before:
        fail("runtime material/package authority changed while validating panels")
    return {
        "panels": meshes,
        "runtime_materials": runtime_materials,
        "panel_count": 11,
        "authored_lod_count": 33,
        "new_texture_count": 0,
        "new_material_count": 0,
        "runtime_package_sha256_before": runtime_before,
        "runtime_package_sha256_after": runtime_after,
    }


def write_json(path: Path, payload: dict) -> None:
    root = run_root()
    if path.parent.resolve() != root or path.name not in RESULT_NAMES:
        fail("attempted write outside current guarded result root")
    if path.exists():
        fail("refusing to overwrite current result evidence: " + str(path))
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
