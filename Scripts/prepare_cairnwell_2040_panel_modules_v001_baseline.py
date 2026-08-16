"""Freeze/reverify the full project baseline for the 11-panel import lane.

Offline standard Python only.  The only creation writes are this lane's new
baseline JSON and SHA-256 sidecar.  It snapshots every approved panel source,
all existing Content outside the absent fresh panel destination (including the
separate runtime materials), Source, Config, project descriptor, campaign
saves, and every prepared lane file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8").resolve()
CONTRACT = PROJECT / "Scripts/cairnwell_2040_panel_modules_v001_import_contract.json"
CONTRACT_SHA = PROJECT / "Scripts/cairnwell_2040_panel_modules_v001_import_contract.sha256"
BASELINE = PROJECT / "Scripts/cairnwell_2040_panel_modules_v001_import_baseline_v002.json"
BASELINE_SHA = PROJECT / "Scripts/cairnwell_2040_panel_modules_v001_import_baseline_v002.sha256"
FAILED_BASELINE_V001 = (
    PROJECT / "Scripts/cairnwell_2040_panel_modules_v001_import_baseline.json"
)
FAILED_BASELINE_V001_SHA = (
    PROJECT / "Scripts/cairnwell_2040_panel_modules_v001_import_baseline.sha256"
)
DEST_DISK = PROJECT / (
    "Content/LineBoss/Factory/OneFactory/v001/Vehicles/"
    "Cairnwell2040PanelModules_v001"
)
AUDIT_ROOT = PROJECT / (
    "Saved/Audits/OneFactory/Vehicles/Cairnwell2040PanelModules_v001/"
    "UnrealImportLane_v001"
)
ACK_TOKEN = (
    "FREEZE_CAIRNWELL_2040_PANEL_MODULES_V001_FULL_BASELINE_V002_AFTER_SOURCE_QUIESCENCE"
)
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
PAINT_PRESENTATION_SOURCE = (
    PROJECT / "Source/LineBossCarFactory/LBOneFactoryPaintStarterPresentationActor.cpp"
)
FAILED_BASELINE_V001_PAINT_ROW = {
    "path": "Source/LineBossCarFactory/LBOneFactoryPaintStarterPresentationActor.cpp",
    "bytes": 56039,
    "mtime_ns": 1786817726204986800,
    "sha256": "465AAC3D0E81618103E7B6CFD04B83B340EAFE3AAC67D9BD956ECCC91C0FCB4C",
}
EXPECTED_POST_CUT_PAINT_ROW = {
    "path": "Source/LineBossCarFactory/LBOneFactoryPaintStarterPresentationActor.cpp",
    "bytes": 56097,
    "mtime_ns": 1786817901526155400,
    "sha256": "A186D6550930B10DFC2D85E7511A5B6D3AC7C5EAFE98CB6026849859D9C4D84A",
}
IMPORT_PASS = (
    "PASS__CAIRNWELL_2040_PANEL_MODULES_V001_FRESH_IMPORT__"
    "11_MESHES__33_AUTHORED_LODS__ZERO_NEW_TEXTURES_MATERIALS__EXACT_11_PACKAGES"
)
VALIDATION_PASS = (
    "PASS__CAIRNWELL_2040_PANEL_MODULES_V001_DISTINCT_FRESH_PROCESS__"
    "READ_ONLY_RELOAD__11_PANEL_PACKAGE_AND_11_RUNTIME_PACKAGE_HASHES_UNCHANGED"
)
SUMMARY_PASS = (
    "PASS__CAIRNWELL_2040_PANEL_MODULES_V001_GUARDED_IMPORT_AND_"
    "DISTINCT_READ_ONLY_RELOAD"
)
RESULT_NAMES = {
    "import_receipt_v001.json",
    "import_failure_v001.json",
    "fresh_process_validation_receipt_v001.json",
    "fresh_process_validation_failure_v001.json",
    "lane_summary_v001.json",
}
RUNTIME_V013_CONTRACT_SHA256 = (
    "5D2B1929086AD33A8354ED0759509BCC6AFFEF8CD4E5BDE77A54546B53E95F12"
)
RUNTIME_V013_RUN_ID = "20260815T172802Z-1389784f"
CACHE_ROOT = PROJECT / "Intermediate/CachedAssetRegistry"
LEGACY_CACHE_MONOLITHIC = PROJECT / "Intermediate/CachedAssetRegistry.bin"


class BaselineError(RuntimeError):
    """Fail-closed baseline error."""


def strict_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise BaselineError(f"duplicate raw JSON property forbidden: {key!r}")
        result[key] = value
    return result


def strict_json(path: Path, label: str) -> dict:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8-sig"), object_pairs_hook=strict_pairs
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise BaselineError(f"{label} JSON is unreadable") from exc
    if not isinstance(value, dict):
        raise BaselineError(f"{label} must be a JSON object")
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
        raise BaselineError(f"path escapes exact project: {path}") from exc


def inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def file_row(path: Path) -> dict:
    if not path.is_file():
        raise BaselineError(f"required baseline file missing: {path}")
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


def inventory(paths: list[Path]) -> dict:
    unique = {relative(path): path for path in paths}
    rows = [file_row(unique[key]) for key in sorted(unique, key=str.casefold)]
    return {"file_count": len(rows), "inventory_sha256": canonical_hash(rows), "files": rows}


def load_contract() -> tuple[dict, str]:
    if not CONTRACT.is_file() or not CONTRACT_SHA.is_file():
        raise BaselineError("approved panel contract and sidecar are absent")
    digest = sha256(CONTRACT)
    if CONTRACT_SHA.read_text(encoding="ascii").strip().split()[0].upper() != digest:
        raise BaselineError("panel contract sidecar drift")
    payload = strict_json(CONTRACT, "panel contract")
    destination = payload.get("destination", {})
    runtime = payload.get("runtime_authority", {})
    policy = payload.get("policy", {})
    if (
        payload.get("$schema")
        != "lineboss/cairnwell-2040-panel-modules-v001/unreal-import-contract/v1"
        or payload.get("status") != CONTRACT_STATUS
        or destination.get("namespace")
        != "/Game/LineBoss/Factory/OneFactory/v001/Vehicles/Cairnwell2040PanelModules_v001"
        or int(destination.get("expected_mesh_count", -1)) != 11
        or int(destination.get("expected_authored_lod_count", -1)) != 33
        or int(destination.get("expected_texture_count", -1)) != 0
        or int(destination.get("expected_material_count", -1)) != 0
        or int(destination.get("expected_package_count", -1)) != 11
        or runtime.get("persisted_dependency_closure_verified") is not True
        or runtime.get("all_package_hashes_unchanged") is not True
        or set(runtime.get("materials", {}))
        != {"biw_galvanised", "ed_coat", "player_paint"}
        or runtime.get("recovery_v013_contract_sha256")
        != RUNTIME_V013_CONTRACT_SHA256
        or runtime.get("recovery_v013_run_id") != RUNTIME_V013_RUN_ID
        or runtime.get("cache_and_legacy_surfaces_unchanged") is not True
        or runtime.get("no_build_tool_invoked") is not True
        or runtime.get("vehicle_model_id") != "CAIRNWELL_2040"
        or runtime.get("production_recipe_id")
        != "CAIRNWELL_2040_DEVELOPMENT_RECIPE_V001"
        or runtime.get("final_release_visual_lock_claimed") is not False
        or runtime.get(
            "historical_v013_project_snapshots_are_receipt_evidence_not_live_baseline"
        ) is not True
        or runtime.get("current_project_authority_is_the_new_panel_baseline") is not True
        or payload.get("material_reuse", {}).get("default_role") != "player_paint"
        or payload.get("project_authority_boundary", {}).get(
            "runtime_v013_project_snapshots_role"
        ) != "HISTORICAL_VALIDATION_EVIDENCE_ONLY"
        or payload.get("project_authority_boundary", {}).get(
            "current_project_authority"
        ) != "NEW_PANEL_BASELINE_FULL_PROJECT_SNAPSHOT"
        or payload.get("project_authority_boundary", {}).get(
            "authorized_intervening_source_evolution"
        ) != "PAINT_PRESENTATION_SOURCE_EVOLUTION"
        or payload.get("project_authority_boundary", {}).get(
            "unrelated_future_drift_authorized"
        ) is not False
        or policy.get("overwrite_reimport_delete_authorized") is not False
        or policy.get("map_load_save_authorized") is not False
        or policy.get("runtime_authority_mutation_authorized") is not False
        or policy.get(
            "post_v013_authorized_source_evolution_must_be_frozen_by_panel_baseline"
        ) is not True
        or policy.get(
            "historical_v013_project_snapshot_may_not_replace_current_panel_baseline"
        ) is not True
        or policy.get("unrelated_post_panel_baseline_drift_authorized") is not False
    ):
        raise BaselineError("panel contract identity/count/runtime/safety drift")
    return payload, digest


def failed_baseline_v001_evidence() -> dict:
    if not FAILED_BASELINE_V001.is_file() or not FAILED_BASELINE_V001_SHA.is_file():
        raise BaselineError("preserved failed baseline v001 pair is absent")
    if sha256(FAILED_BASELINE_V001) != FAILED_BASELINE_V001_SHA256:
        raise BaselineError("preserved failed baseline v001 payload drift")
    if sha256(FAILED_BASELINE_V001_SHA) != FAILED_BASELINE_V001_SIDECAR_FILE_SHA256:
        raise BaselineError("preserved failed baseline v001 sidecar file drift")
    sidecar_tokens = FAILED_BASELINE_V001_SHA.read_text(encoding="ascii").strip().split()
    if sidecar_tokens != [FAILED_BASELINE_V001_SHA256, FAILED_BASELINE_V001.name]:
        raise BaselineError("preserved failed baseline v001 sidecar token/name drift")
    payload = strict_json(FAILED_BASELINE_V001, "preserved failed baseline v001")
    if (
        payload.get("$schema")
        != "lineboss/cairnwell-2040-panel-modules-v001/unreal-import-baseline/v1"
        or payload.get("status")
        != "FROZEN__CAIRNWELL_2040_PANEL_MODULES_V001_PROJECT_BASELINE"
    ):
        raise BaselineError("preserved failed baseline v001 identity drift")
    captured_rows = {
        item.get("path"): item for item in payload.get("protected", {}).get("files", [])
    }
    if captured_rows.get(FAILED_BASELINE_V001_PAINT_ROW["path"]) != FAILED_BASELINE_V001_PAINT_ROW:
        raise BaselineError("failed baseline v001 Paint row drift")
    observed = file_row(PAINT_PRESENTATION_SOURCE)
    if observed != EXPECTED_POST_CUT_PAINT_ROW:
        raise BaselineError("post-cut Paint Source authority is not quiescent/exact")
    if observed == FAILED_BASELINE_V001_PAINT_ROW:
        raise BaselineError("failed baseline v001 no longer proves the captured drift")
    return {
        "status": (
            "PRESERVED__UNSELECTABLE__FAILED_IMMEDIATE_REVERIFICATION__"
            "CONCURRENT_AUTHORIZED_PAINT_SOURCE_DRIFT"
        ),
        "baseline": file_row(FAILED_BASELINE_V001),
        "sidecar": file_row(FAILED_BASELINE_V001_SHA),
        "captured_paint_source": FAILED_BASELINE_V001_PAINT_ROW,
        "observed_post_cut_paint_source": observed,
        "may_authorize_unreal": False,
        "may_be_selected_as_current_baseline": False,
    }


def source_snapshot(contract: dict) -> dict:
    rows = []
    seen = set()
    for expected in contract["provenance"]["source_files"]:
        actual = file_row(PROJECT / expected["path"])
        if (
            actual["bytes"] != int(expected["bytes"])
            or actual["sha256"] != expected["sha256"]
            or actual["path"] in seen
        ):
            raise BaselineError(f"approved panel source drift/duplicate: {expected['path']}")
        seen.add(actual["path"])
        rows.append(actual)
    return {
        "file_count": len(rows),
        "inventory_sha256": canonical_hash(rows),
        "files": sorted(rows, key=lambda item: item["path"].casefold()),
    }


def runtime_snapshot(contract: dict) -> dict:
    runtime = contract["runtime_authority"]
    evidence_keys = (
        "contract", "contract_sidecar", "baseline", "baseline_sidecar",
        "recovery_v013_contract", "recovery_v013_contract_sidecar",
        "fresh_validation_receipt", "lane_summary",
    )
    paths = [
        PROJECT / runtime[key]["path"]
        for key in evidence_keys
    ]
    paths.extend(
        PROJECT / item["path"]
        for item in runtime["recovery_v013_result_files"].values()
    )
    for package in runtime["package_sha256"]:
        paths.append(PROJECT / ("Content/" + package.removeprefix("/Game/") + ".uasset"))
    snapshot = inventory(paths)
    rows = {item["path"]: item for item in snapshot["files"]}
    for key in evidence_keys:
        expected = runtime[key]
        actual = rows.get(expected["path"])
        if actual is None or actual["bytes"] != expected["bytes"] or actual["sha256"] != expected["sha256"]:
            raise BaselineError(f"approved runtime evidence drift: {key}")
    for filename, expected in runtime["recovery_v013_result_files"].items():
        actual = rows.get(expected["path"])
        if (
            actual is None
            or actual["bytes"] != expected["bytes"]
            or actual["sha256"] != expected["sha256"]
        ):
            raise BaselineError(f"exact runtime V013 result drift: {filename}")
    for package, digest in runtime["package_sha256"].items():
        rel = "Content/" + package.removeprefix("/Game/") + ".uasset"
        if rows.get(rel, {}).get("sha256") != digest:
            raise BaselineError(f"approved runtime package drift: {package}")
    return snapshot


def scan(root: Path, excludes: tuple[Path, ...] = ()) -> list[Path]:
    if not root.is_dir():
        return []
    return [
        path for path in root.rglob("*")
        if path.is_file()
        and not any(path.resolve() == item.resolve() or inside(path, item) for item in excludes)
    ]


def protected_snapshot() -> dict:
    descriptor = PROJECT / "LineBossCarFactory.uproject"
    groups = [
        ("project_descriptor", [], [descriptor], [], False),
        ("complete_source_tree", ["Source"], scan(PROJECT / "Source"), [], False),
        ("complete_config_tree", ["Config"], scan(PROJECT / "Config"), [], False),
        (
            "all_existing_content_outside_panel_destination_including_maps_and_runtime",
            ["Content"],
            scan(PROJECT / "Content", (DEST_DISK,)),
            [relative(DEST_DISK)],
            False,
        ),
        ("campaign_save_games", ["Saved/SaveGames"], scan(PROJECT / "Saved/SaveGames"), [], True),
    ]
    union: dict[str, Path] = {}
    group_rows = []
    for name, roots, selected, excludes, allow_empty in groups:
        if not selected and not allow_empty:
            raise BaselineError(f"protected group unexpectedly empty: {name}")
        paths = sorted({relative(path) for path in selected}, key=str.casefold)
        group_rows.append({
            "name": name,
            "roots": roots,
            "files": [relative(descriptor)] if name == "project_descriptor" else [],
            "excludes": excludes,
            "allow_empty": allow_empty,
            "paths": paths,
        })
        union.update({relative(path): path for path in selected})
    result = inventory(list(union.values()))
    result["groups"] = group_rows
    return result


def lane_snapshot(contract: dict) -> dict:
    paths = [CONTRACT, CONTRACT_SHA, FAILED_BASELINE_V001, FAILED_BASELINE_V001_SHA]
    paths.extend(PROJECT / value for value in contract["lane_files_to_pin_when_baseline_is_cut"])
    return inventory(paths)


def prior_results() -> list[str]:
    if not AUDIT_ROOT.is_dir():
        return []
    return sorted(
        relative(path) for path in AUDIT_ROOT.rglob("*")
        if path.is_file() and path.name in RESULT_NAMES
    )


def asset_registry_cache_snapshot() -> dict:
    if not CACHE_ROOT.is_dir():
        raise BaselineError("Intermediate/CachedAssetRegistry is absent")
    result = inventory([path for path in CACHE_ROOT.rglob("*") if path.is_file()])
    result["root"] = relative(CACHE_ROOT)
    if result["file_count"] != 2:
        raise BaselineError("asset-registry cache must remain the exact two-file V013 surface")
    return result


def legacy_asset_registry_cache_absence() -> dict:
    intermediate = PROJECT / "Intermediate"
    legacy_shards = sorted(
        (
            path for path in intermediate.iterdir()
            if path.is_file()
            and path.name.casefold().startswith("cachedassetregistry_")
            and path.name.casefold().endswith(".bin")
        ),
        key=lambda path: path.name.casefold(),
    ) if intermediate.is_dir() else []
    result = {
        "root": "Intermediate",
        "monolithic_path": "Intermediate/CachedAssetRegistry.bin",
        "monolithic_absent": not any(
            path.is_file() and path.name.casefold() == "cachedassetregistry.bin"
            for path in intermediate.iterdir()
        ) if intermediate.is_dir() else True,
        "legacy_shard_pattern": "Intermediate/CachedAssetRegistry_*.bin",
        "legacy_shard_paths": [relative(path) for path in legacy_shards],
        "matching_path_count": len(legacy_shards),
        "windows_case_insensitive_name_match": True,
    }
    if result["monolithic_absent"] is not True or result["matching_path_count"] != 0:
        raise BaselineError("legacy asset-registry cache deletion surface is not absent")
    return result


def create(acknowledgement: str) -> None:
    if acknowledgement != ACK_TOKEN:
        raise BaselineError("exact panel baseline acknowledgement missing")
    if BASELINE.exists() or BASELINE_SHA.exists():
        raise BaselineError("refusing to overwrite an existing panel baseline or sidecar")
    if DEST_DISK.exists():
        raise BaselineError("fresh panel destination already exists")
    if AUDIT_ROOT.exists():
        raise BaselineError("one-shot panel audit root already exists")
    contract, digest = load_contract()
    failed_v001 = failed_baseline_v001_evidence()
    cache = asset_registry_cache_snapshot()
    legacy_cache = legacy_asset_registry_cache_absence()
    if (
        cache != contract["runtime_authority"]["asset_registry_cache"]
        or legacy_cache
        != contract["runtime_authority"]["legacy_asset_registry_cache_absence"]
    ):
        raise BaselineError("current cache surfaces differ from definitive runtime V013 PASS")
    source = source_snapshot(contract)
    runtime = runtime_snapshot(contract)
    protected = protected_snapshot()
    lane = lane_snapshot(contract)
    authority_boundary = {
        "runtime_v013_project_snapshots_role": "HISTORICAL_VALIDATION_EVIDENCE_ONLY",
        "historical_runtime_v013": {
            "source": contract["runtime_authority"]["historical_v013_source_snapshot"],
            "protected": contract["runtime_authority"][
                "historical_v013_protected_snapshot"
            ],
            "prepared_lane": contract["runtime_authority"][
                "historical_v013_prepared_lane_snapshot"
            ],
        },
        "current_project_authority": "THIS_PANEL_BASELINE_FULL_PROJECT_SNAPSHOT",
        "current_protected_file_count": protected["file_count"],
        "current_protected_inventory_sha256": protected["inventory_sha256"],
        "authorized_intervening_source_evolution":
            "PAINT_PRESENTATION_SOURCE_EVOLUTION",
        "observed_post_cut_paint_source": failed_v001[
            "observed_post_cut_paint_source"
        ],
        "authorized_intervening_source_evolution_is_now_frozen": True,
        "unrelated_future_drift_authorized": False,
    }
    payload = {
        "$schema": BASELINE_SCHEMA,
        "status": BASELINE_STATUS,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": str(PROJECT),
        "contract": {"path": relative(CONTRACT), "sha256": digest},
        "destination": contract["destination"],
        "shared_datum": contract["shared_datum"],
        "runtime_authority": contract["runtime_authority"],
        "superseded_failed_baseline_v001": failed_v001,
        "project_authority_boundary": authority_boundary,
        "material_reuse": contract["material_reuse"],
        "modules": contract["modules"],
        "import_contract": contract["import_contract"],
        "source": source,
        "runtime": runtime,
        "asset_registry_cache": cache,
        "legacy_asset_registry_cache_absence": legacy_cache,
        "protected": protected,
        "lane": lane,
        "policy": contract["policy"],
    }
    if (
        source_snapshot(contract) != source
        or runtime_snapshot(contract) != runtime
        or protected_snapshot() != protected
        or lane_snapshot(contract) != lane
        or asset_registry_cache_snapshot() != cache
        or legacy_asset_registry_cache_absence() != legacy_cache
        or failed_baseline_v001_evidence() != failed_v001
    ):
        raise BaselineError("project changed during the pre-write baseline snapshot")
    BASELINE.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    baseline_digest = sha256(BASELINE)
    BASELINE_SHA.write_text(f"{baseline_digest}  {BASELINE.name}\n", encoding="ascii")
    print("PASS__CAIRNWELL_2040_PANEL_MODULES_V001_PROJECT_BASELINE_V002_FROZEN")
    print(baseline_digest)


def verify_inventory(snapshot: dict, label: str) -> None:
    rows = []
    for expected in snapshot["files"]:
        actual = file_row(PROJECT / expected["path"])
        if any(actual[key] != expected[key] for key in ("path", "bytes", "mtime_ns", "sha256")):
            raise BaselineError(f"{label} file drift: {expected['path']}")
        rows.append(actual)
    if len(rows) != int(snapshot["file_count"]) or canonical_hash(rows) != snapshot["inventory_sha256"]:
        raise BaselineError(f"{label} inventory drift")


def verify_protected_paths(snapshot: dict) -> None:
    union = set()
    for group in snapshot["groups"]:
        selected = {PROJECT / rel for rel in group.get("files", [])}
        for root in group.get("roots", []):
            selected.update(scan(PROJECT / root, tuple(PROJECT / rel for rel in group.get("excludes", []))))
        paths = {relative(path) for path in selected}
        if paths != set(group["paths"]):
            raise BaselineError(f"protected path inventory drift: {group['name']}")
        union.update(paths)
    if union != {item["path"] for item in snapshot["files"]}:
        raise BaselineError("protected group union drift")


def load_frozen() -> tuple[dict, str]:
    contract, contract_digest = load_contract()
    if not BASELINE.is_file() or not BASELINE_SHA.is_file():
        raise BaselineError("panel baseline or sidecar is absent")
    digest = sha256(BASELINE)
    if BASELINE_SHA.read_text(encoding="ascii").strip().split()[0].upper() != digest:
        raise BaselineError("panel baseline sidecar drift")
    payload = strict_json(BASELINE, "panel baseline")
    if (
        payload.get("$schema")
        != BASELINE_SCHEMA
        or payload.get("status") != BASELINE_STATUS
        or payload.get("contract", {}).get("sha256") != contract_digest
        or payload.get("destination") != contract.get("destination")
        or payload.get("shared_datum") != contract.get("shared_datum")
        or payload.get("runtime_authority") != contract.get("runtime_authority")
        or payload.get("superseded_failed_baseline_v001")
        != failed_baseline_v001_evidence()
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
            "observed_post_cut_paint_source"
        ) != EXPECTED_POST_CUT_PAINT_ROW
        or payload.get("project_authority_boundary", {}).get(
            "unrelated_future_drift_authorized"
        ) is not False
        or payload.get("material_reuse") != contract.get("material_reuse")
        or payload.get("modules") != contract.get("modules")
        or payload.get("import_contract") != contract.get("import_contract")
        or payload.get("policy") != contract.get("policy")
    ):
        raise BaselineError("frozen panel baseline no longer binds the exact contract")
    return payload, digest


def verify_immutable(payload: dict) -> None:
    verify_inventory(payload["source"], "approved panel source")
    verify_inventory(payload["runtime"], "approved runtime authority")
    verify_protected_paths(payload["protected"])
    verify_inventory(payload["protected"], "protected project")
    verify_inventory(payload["lane"], "prepared panel lane")
    if asset_registry_cache_snapshot() != payload["asset_registry_cache"]:
        raise BaselineError("asset-registry cache changed from frozen panel baseline")
    if legacy_asset_registry_cache_absence() != payload[
        "legacy_asset_registry_cache_absence"
    ]:
        raise BaselineError("legacy asset-registry cache absence changed")


def verify() -> None:
    payload, digest = load_frozen()
    if DEST_DISK.exists() or AUDIT_ROOT.exists():
        raise BaselineError(
            "pre-import baseline verification requires absent destination and audit root"
        )
    boundary = payload["project_authority_boundary"]
    if (
        boundary.get("current_protected_file_count")
        != payload["protected"]["file_count"]
        or boundary.get("current_protected_inventory_sha256")
        != payload["protected"]["inventory_sha256"]
    ):
        raise BaselineError("current panel project authority boundary drift")
    verify_immutable(payload)
    print("PASS__CAIRNWELL_2040_PANEL_MODULES_V001_FULL_BASELINE_REVERIFIED")
    print(digest)


def verify_post_import_immutable() -> None:
    payload, digest = load_frozen()
    verify_immutable(payload)
    print("PASS__CAIRNWELL_2040_PANEL_MODULES_V001_POST_IMPORT_IMMUTABLE_REVERIFIED")
    print(digest)


def exact_int(value, label: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise BaselineError(f"{label} must be an exact integer >= {minimum}")
    return value


def panel_package_hashes(payload: dict) -> dict[str, str]:
    answer = {}
    for package in payload["destination"]["expected_package_paths"]:
        path = PROJECT / ("Content/" + package.removeprefix("/Game/") + ".uasset")
        answer[package] = sha256(path)
    actual = {
        "/Game/" + path.relative_to(PROJECT / "Content").with_suffix("").as_posix()
        for path in DEST_DISK.rglob("*.uasset")
    } if DEST_DISK.is_dir() else set()
    if actual != set(answer) or len(answer) != 11:
        raise BaselineError("panel destination is not the exact 11-package closure")
    return answer


def inventory_identity(snapshot: dict) -> dict:
    return {
        "file_count": int(snapshot["file_count"]),
        "inventory_sha256": str(snapshot["inventory_sha256"]),
    }


def runtime_identity(payload: dict) -> dict:
    return {
        **inventory_identity(payload["runtime"]),
        "package_sha256": payload["runtime_authority"]["package_sha256"],
    }


def process_log_evidence(run_root: Path, stem: str, pass_marker: str) -> dict:
    paths = {
        "log": run_root / f"{stem}.log",
        "stdout": run_root / f"{stem}.stdout.log",
        "stderr": run_root / f"{stem}.stderr.log",
    }
    if paths["stderr"].read_bytes() != b"":
        raise BaselineError(f"{stem} redirected stderr is not empty")
    texts = {
        key: path.read_text(encoding="utf-8", errors="replace")
        for key, path in paths.items()
    }
    combined = "\n".join(texts.values())
    fatal = (
        "Fatal error:", "Assertion failed:", "Unhandled Exception:",
        "appError called", "Ensure condition failed", "ModeManager",
        "ModeManagerInteractiveToolsContext", "Launching UnrealBuildTool",
        "UnrealBuildTool", "Build.bat", "-Mode=ValidatePlatforms",
        "AutoSDKInfo.txt", "UBT AutoSDK ReturnCode",
        "Asset registry cache written as", "deleted (orphaned",
        "delete failed (orphaned", "CleanupOrphanedCacheFiles: legacy location",
    )
    found = [token for token in fatal if token.casefold() in combined.casefold()]
    if found:
        raise BaselineError(f"{stem} fatal/ensure/UBT/cache-mutation log gate: {found}")
    preload = (
        "CleanupOrphanedCacheFiles (PreLoad): 1 .ref files found, "
        "1 referenced binaries"
    )
    postwrite = (
        "CleanupOrphanedCacheFiles (PostWrite): 1 .ref files found, "
        "1 referenced binaries"
    )
    zero = (
        "CleanupOrphanedCacheFiles: 1 total binaries, 1 referenced (kept), "
        "0 old-style pre-migration (kept), 0 orphans deleted, "
        "0 orphans locked (kept)"
    )
    cleanup = {}
    for key in ("log", "stdout"):
        lines = texts[key].splitlines()
        pre = [index for index, line in enumerate(lines) if line.endswith(preload)]
        post = [index for index, line in enumerate(lines) if line.endswith(postwrite)]
        zeros = [index for index, line in enumerate(lines) if line.endswith(zero)]
        if (
            len(pre) != 1 or len(post) != 1 or len(zeros) != 2
            or pre[0] + 1 not in zeros or post[0] + 1 not in zeros
        ):
            raise BaselineError(f"{stem}:{key} exact zero-mutation cleanup topology drift")
        if texts[key].count(pass_marker) != 1 or texts[key].count("LogExit: Exiting.") != 1:
            raise BaselineError(f"{stem}:{key} PASS/natural-exit marker cardinality drift")
        cleanup[key] = {
            "preload_occurrences": 1,
            "postwrite_occurrences": 1,
            "adjacent_zero_mutation_occurrences": 2,
        }
    return {
        "log_sha256": sha256(paths["log"]),
        "stdout_sha256": sha256(paths["stdout"]),
        "stderr_sha256": sha256(paths["stderr"]),
        "fatal_or_build_tool_log_patterns": [],
        "natural_execute_python_script_exit_verified": True,
        "asset_registry_cache_cleanup": cleanup,
    }


def checked_run_root(value: Path) -> Path:
    root = value.resolve()
    if root.parent.resolve() != AUDIT_ROOT.resolve() or not root.is_dir():
        raise BaselineError("panel run root is absent or not a direct audit child")
    return root


def verify_import_result(run_root_value: Path) -> dict:
    run_root = checked_run_root(run_root_value)
    payload, baseline_digest = load_frozen()
    verify_immutable(payload)
    expected_names = {
        "import_receipt_v001.json", "unreal_import.log",
        "unreal_import.stdout.log", "unreal_import.stderr.log",
    }
    actual_names = {path.name for path in run_root.iterdir() if path.is_file()}
    if actual_names != expected_names or any(path.is_dir() for path in run_root.iterdir()):
        raise BaselineError("first process did not leave exact four-file PASS closure")
    receipt_path = run_root / "import_receipt_v001.json"
    receipt = strict_json(receipt_path, "panel import receipt")
    packages = panel_package_hashes(payload)
    source_identity = inventory_identity(payload["source"])
    protected_identity = inventory_identity(payload["protected"])
    lane_identity = inventory_identity(payload["lane"])
    approved_runtime = runtime_identity(payload)
    cvar = receipt.get("interchange_fbx_legacy_custom_lod_guard", {})
    if (
        receipt.get("$schema")
        != "lineboss/audit/cairnwell-2040-panel-modules-v001/unreal-import/v1"
        or receipt.get("status") != IMPORT_PASS
        or receipt.get("contract_sha256") != payload["contract"]["sha256"]
        or receipt.get("baseline_sha256") != baseline_digest
        or receipt.get("panel_package_sha256") != packages
        or receipt.get("mesh_count") != 11
        or receipt.get("authored_lod_count") != 33
        or receipt.get("texture_count") != 0
        or receipt.get("material_count") != 0
        or receipt.get("package_count") != 11
        or receipt.get("runtime_packages_unchanged") is not True
        or receipt.get("source_before") != source_identity
        or receipt.get("source_after") != source_identity
        or receipt.get("protected_before") != protected_identity
        or receipt.get("protected_after") != protected_identity
        or receipt.get("prepared_lane_before") != lane_identity
        or receipt.get("prepared_lane_after") != lane_identity
        or receipt.get("runtime_before") != approved_runtime
        or receipt.get("runtime_after") != approved_runtime
        or receipt.get("project_maps_loaded_or_saved") != []
        or receipt.get("asset_registry_cache_before") != payload["asset_registry_cache"]
        or receipt.get("asset_registry_cache_after") != payload["asset_registry_cache"]
        or receipt.get("legacy_asset_registry_cache_absence_before")
        != payload["legacy_asset_registry_cache_absence"]
        or receipt.get("legacy_asset_registry_cache_absence_after")
        != payload["legacy_asset_registry_cache_absence"]
        or receipt.get("no_asset_registry_cache_write_command_line_verified") is not True
        or receipt.get("ubt_startup_guard_environment", {}).get("observed_value") != "1"
        or receipt.get("vehicle_model_id") != "CAIRNWELL_2040"
        or receipt.get("final_release_visual_lock_claimed") is not False
        or receipt.get("strict_lod_uv_clean_edges_bounds_shared_origin_material_gates_verified")
        is not True
        or receipt.get("nanite_collision_navigation_off_verified") is not True
        or cvar.get("name") != "Interchange.FeatureFlags.Import.FBX"
        or cvar.get("custom_lods_requested") != 22
        or len(cvar.get("custom_lods_imported", [])) != 22
        or cvar.get("restore_attempted_in_finally") is not True
        or cvar.get("restored_value") != cvar.get("previous_value")
    ):
        raise BaselineError("panel import receipt identity/package/cache/safety drift")
    process_id = exact_int(receipt.get("process_id"), "panel importer process_id", 1)
    logs = process_log_evidence(
        run_root, "unreal_import",
        "LINE_BOSS_CAIRNWELL_2040_PANEL_MODULES_V001_IMPORT_PASS",
    )
    return {
        "receipt": file_row(receipt_path),
        "process_id": process_id,
        "package_sha256": packages,
        "logs": logs,
    }


def verify_validation_result(run_root_value: Path, allow_summary: bool = False) -> dict:
    run_root = checked_run_root(run_root_value)
    payload, baseline_digest = load_frozen()
    verify_immutable(payload)
    expected_names = {
        "import_receipt_v001.json", "unreal_import.log",
        "unreal_import.stdout.log", "unreal_import.stderr.log",
        "fresh_process_validation_receipt_v001.json",
        "fresh_process_validation.log", "fresh_process_validation.stdout.log",
        "fresh_process_validation.stderr.log",
    }
    if allow_summary:
        expected_names.add("lane_summary_v001.json")
    actual_names = {path.name for path in run_root.iterdir() if path.is_file()}
    if actual_names != expected_names or any(path.is_dir() for path in run_root.iterdir()):
        raise BaselineError("two-process pre-summary closure is not exact eight files")
    imported = verify_import_result_with_extra_files(run_root, expected_names)
    receipt_path = run_root / "fresh_process_validation_receipt_v001.json"
    receipt = strict_json(receipt_path, "panel fresh-process receipt")
    packages = imported["package_sha256"]
    import_pid = imported["process_id"]
    validator_pid = exact_int(receipt.get("process_id"), "panel validator process_id", 1)
    if (
        receipt.get("$schema")
        != "lineboss/audit/cairnwell-2040-panel-modules-v001/fresh-process-validation/v1"
        or receipt.get("status") != VALIDATION_PASS
        or receipt.get("contract_sha256") != payload["contract"]["sha256"]
        or receipt.get("baseline_sha256") != baseline_digest
        or receipt.get("import_receipt_sha256") != imported["receipt"]["sha256"]
        or receipt.get("import_process_id") != import_pid
        or receipt.get("validator_process_id") != validator_pid
        or validator_pid == import_pid
        or receipt.get("distinct_process_verified") is not True
        or receipt.get("panel_package_sha256_before_loads") != packages
        or receipt.get("panel_package_sha256_after_loads") != packages
        or receipt.get("mesh_count") != 11
        or receipt.get("authored_lod_count") != 33
        or receipt.get("texture_count") != 0
        or receipt.get("material_count") != 0
        or receipt.get("package_count") != 11
        or receipt.get("asset_mutation_count") != 0
        or receipt.get("asset_mutations") != []
        or receipt.get("all_panel_package_hashes_unchanged") is not True
        or receipt.get("all_runtime_package_hashes_unchanged") is not True
        or receipt.get("persisted_runtime_material_dependencies_verified") is not True
        or receipt.get("source_before") != inventory_identity(payload["source"])
        or receipt.get("source_after") != inventory_identity(payload["source"])
        or receipt.get("protected_before") != inventory_identity(payload["protected"])
        or receipt.get("protected_after") != inventory_identity(payload["protected"])
        or receipt.get("prepared_lane_before") != inventory_identity(payload["lane"])
        or receipt.get("prepared_lane_after") != inventory_identity(payload["lane"])
        or receipt.get("runtime_before") != runtime_identity(payload)
        or receipt.get("runtime_after") != runtime_identity(payload)
        or receipt.get("project_maps_loaded_or_saved") != []
        or receipt.get("asset_registry_cache_before") != payload["asset_registry_cache"]
        or receipt.get("asset_registry_cache_after") != payload["asset_registry_cache"]
        or receipt.get("legacy_asset_registry_cache_absence_before")
        != payload["legacy_asset_registry_cache_absence"]
        or receipt.get("legacy_asset_registry_cache_absence_after")
        != payload["legacy_asset_registry_cache_absence"]
        or receipt.get("no_asset_registry_cache_write_command_line_verified") is not True
        or receipt.get("ubt_startup_guard_environment", {}).get("observed_value") != "1"
    ):
        raise BaselineError("panel fresh-process receipt identity/package/cache/safety drift")
    logs = process_log_evidence(
        run_root, "fresh_process_validation",
        "LINE_BOSS_CAIRNWELL_2040_PANEL_MODULES_V001_FRESH_VALIDATION_PASS",
    )
    return {
        "receipt": file_row(receipt_path),
        "process_id": validator_pid,
        "package_sha256": packages,
        "logs": logs,
        "import": imported,
    }


def verify_import_result_with_extra_files(run_root: Path, allowed_names: set[str]) -> dict:
    """Same exact import receipt/log checks after the validator added its four files."""
    payload, baseline_digest = load_frozen()
    receipt_path = run_root / "import_receipt_v001.json"
    receipt = strict_json(receipt_path, "panel import receipt")
    packages = panel_package_hashes(payload)
    if (
        {path.name for path in run_root.iterdir() if path.is_file()} != allowed_names
        or receipt.get("status") != IMPORT_PASS
        or receipt.get("contract_sha256") != payload["contract"]["sha256"]
        or receipt.get("baseline_sha256") != baseline_digest
        or receipt.get("panel_package_sha256") != packages
        or receipt.get("source_before") != inventory_identity(payload["source"])
        or receipt.get("source_after") != inventory_identity(payload["source"])
        or receipt.get("protected_before") != inventory_identity(payload["protected"])
        or receipt.get("protected_after") != inventory_identity(payload["protected"])
        or receipt.get("prepared_lane_before") != inventory_identity(payload["lane"])
        or receipt.get("prepared_lane_after") != inventory_identity(payload["lane"])
        or receipt.get("runtime_before") != runtime_identity(payload)
        or receipt.get("runtime_after") != runtime_identity(payload)
        or receipt.get("asset_registry_cache_before") != payload["asset_registry_cache"]
        or receipt.get("asset_registry_cache_after") != payload["asset_registry_cache"]
    ):
        raise BaselineError("panel import evidence drift after validator")
    return {
        "receipt": file_row(receipt_path),
        "process_id": exact_int(receipt.get("process_id"), "panel importer process_id", 1),
        "package_sha256": packages,
        "logs": process_log_evidence(
            run_root, "unreal_import",
            "LINE_BOSS_CAIRNWELL_2040_PANEL_MODULES_V001_IMPORT_PASS",
        ),
    }


def finalize_result(run_root_value: Path, import_exit: int, validation_exit: int) -> None:
    if import_exit != 0 or validation_exit != 0:
        raise BaselineError("both distinct Unreal processes must exit exactly zero")
    run_root = checked_run_root(run_root_value)
    validation = verify_validation_result(run_root)
    payload, baseline_digest = load_frozen()
    summary_path = run_root / "lane_summary_v001.json"
    if summary_path.exists():
        raise BaselineError("refusing to overwrite panel lane summary")
    imported = validation["import"]
    summary = {
        "$schema": "lineboss/audit/cairnwell-2040-panel-modules-v001/import-lane-summary/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": SUMMARY_PASS,
        "run_root": relative(run_root),
        "contract_sha256": payload["contract"]["sha256"],
        "baseline_sha256": baseline_digest,
        "runtime_recovery_v013_contract_sha256": RUNTIME_V013_CONTRACT_SHA256,
        "runtime_recovery_v013_run_id": RUNTIME_V013_RUN_ID,
        "vehicle_model_id": "CAIRNWELL_2040",
        "production_recipe_id": "CAIRNWELL_2040_DEVELOPMENT_RECIPE_V001",
        "development_geometry_revisionable": True,
        "final_release_visual_lock_claimed": False,
        "import_process": {
            "process_id": imported["process_id"], "exit_code": 0,
            **imported["logs"],
        },
        "validation_process": {
            "process_id": validation["process_id"], "exit_code": 0,
            **validation["logs"],
        },
        "import_receipt": imported["receipt"],
        "fresh_validation_receipt": validation["receipt"],
        "post_exit_panel_package_sha256": validation["package_sha256"],
        "runtime_package_sha256": payload["runtime_authority"]["package_sha256"],
        "post_exit_asset_registry_cache": asset_registry_cache_snapshot(),
        "post_exit_legacy_asset_registry_cache_absence":
            legacy_asset_registry_cache_absence(),
        "editor_process_count": 2,
        "no_build_tool_invoked": True,
        "exact_ubt_command_line_matches": 0,
        "environment_restoration_verified": True,
        "strict_exit_zero_no_fatal_ensure_and_no_ubt_log_required": True,
        "content_move_delete_reimport_count": 0,
        "error": None,
    }
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("PASS__CAIRNWELL_2040_PANEL_MODULES_V001_SUMMARY_FINALIZED")
    print(sha256(summary_path))


def verify_final_result(run_root_value: Path) -> None:
    run_root = checked_run_root(run_root_value)
    expected_names = {
        "import_receipt_v001.json", "unreal_import.log",
        "unreal_import.stdout.log", "unreal_import.stderr.log",
        "fresh_process_validation_receipt_v001.json",
        "fresh_process_validation.log", "fresh_process_validation.stdout.log",
        "fresh_process_validation.stderr.log", "lane_summary_v001.json",
    }
    if {path.name for path in run_root.iterdir() if path.is_file()} != expected_names:
        raise BaselineError("final panel result is not the exact nine-file closure")
    summary = strict_json(run_root / "lane_summary_v001.json", "panel lane summary")
    validation = verify_validation_result(run_root, allow_summary=True)
    imported = validation["import"]
    fresh = strict_json(run_root / "fresh_process_validation_receipt_v001.json",
                        "panel fresh-process receipt")
    expected_summary_keys = {
        "$schema", "generated_utc", "status", "run_root", "contract_sha256",
        "baseline_sha256", "runtime_recovery_v013_contract_sha256",
        "runtime_recovery_v013_run_id", "vehicle_model_id",
        "production_recipe_id", "development_geometry_revisionable",
        "final_release_visual_lock_claimed", "import_process",
        "validation_process", "import_receipt", "fresh_validation_receipt",
        "post_exit_panel_package_sha256", "runtime_package_sha256",
        "post_exit_asset_registry_cache",
        "post_exit_legacy_asset_registry_cache_absence", "editor_process_count",
        "no_build_tool_invoked", "exact_ubt_command_line_matches",
        "environment_restoration_verified",
        "strict_exit_zero_no_fatal_ensure_and_no_ubt_log_required",
        "content_move_delete_reimport_count", "error",
    }
    expected_import_process = {
        "process_id": imported["process_id"], "exit_code": 0,
        **imported["logs"],
    }
    expected_validation_process = {
        "process_id": validation["process_id"], "exit_code": 0,
        **validation["logs"],
    }
    payload, baseline_digest = load_frozen()
    if (
        set(summary) != expected_summary_keys
        or summary.get("$schema")
        != "lineboss/audit/cairnwell-2040-panel-modules-v001/import-lane-summary/v1"
        or summary.get("status") != SUMMARY_PASS
        or summary.get("runtime_recovery_v013_contract_sha256")
        != RUNTIME_V013_CONTRACT_SHA256
        or summary.get("runtime_recovery_v013_run_id") != RUNTIME_V013_RUN_ID
        or summary.get("contract_sha256") != payload["contract"]["sha256"]
        or summary.get("baseline_sha256") != baseline_digest
        or summary.get("import_process") != expected_import_process
        or summary.get("validation_process") != expected_validation_process
        or summary.get("import_receipt") != imported["receipt"]
        or summary.get("fresh_validation_receipt") != validation["receipt"]
        or summary.get("import_process", {}).get("process_id")
        != imported["process_id"]
        or summary.get("import_process", {}).get("exit_code") != 0
        or summary.get("validation_process", {}).get("process_id")
        != validation["process_id"]
        or summary.get("validation_process", {}).get("exit_code") != 0
        or summary.get("editor_process_count") != 2
        or summary.get("no_build_tool_invoked") is not True
        or summary.get("exact_ubt_command_line_matches") != 0
        or summary.get("environment_restoration_verified") is not True
        or summary.get("strict_exit_zero_no_fatal_ensure_and_no_ubt_log_required")
        is not True
        or summary.get("content_move_delete_reimport_count") != 0
        or summary.get("error") is not None
        or summary.get("post_exit_panel_package_sha256")
        != panel_package_hashes(load_frozen()[0])
        or summary.get("post_exit_asset_registry_cache")
        != asset_registry_cache_snapshot()
        or summary.get("post_exit_legacy_asset_registry_cache_absence")
        != legacy_asset_registry_cache_absence()
        or summary.get("runtime_package_sha256")
        != payload["runtime_authority"]["package_sha256"]
    ):
        raise BaselineError("final panel lane summary binding/safety drift")
    print("PASS__CAIRNWELL_2040_PANEL_MODULES_V001_FINAL_NINE_FILE_REVERIFIED")
    print(sha256(run_root / "lane_summary_v001.json"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--acknowledgement", default="")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--verify-post-import-immutable", action="store_true")
    parser.add_argument("--verify-import-result", type=Path)
    parser.add_argument("--verify-validation-result", type=Path)
    parser.add_argument("--finalize-result", type=Path)
    parser.add_argument("--verify-final-result", type=Path)
    parser.add_argument("--import-exit-code", type=int, default=-1)
    parser.add_argument("--validation-exit-code", type=int, default=-1)
    args = parser.parse_args()
    if args.verify_final_result is not None:
        verify_final_result(args.verify_final_result)
    elif args.finalize_result is not None:
        finalize_result(
            args.finalize_result, args.import_exit_code, args.validation_exit_code
        )
    elif args.verify_validation_result is not None:
        verify_validation_result(args.verify_validation_result)
        print("PASS__CAIRNWELL_2040_PANEL_MODULES_V001_VALIDATION_RESULT_REVERIFIED")
    elif args.verify_import_result is not None:
        verify_import_result(args.verify_import_result)
        print("PASS__CAIRNWELL_2040_PANEL_MODULES_V001_IMPORT_RESULT_REVERIFIED")
    elif args.verify_post_import_immutable:
        verify_post_import_immutable()
    elif args.verify_only:
        verify()
    else:
        create(args.acknowledgement)


if __name__ == "__main__":
    main()
