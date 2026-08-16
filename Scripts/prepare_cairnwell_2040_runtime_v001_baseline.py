"""Create or verify the offline baseline for the approved Cairnwell v005 authority.

This tool is inert until the approved import contract and its sidecar exist.
It imports no Unreal module, starts no process, and never writes outside the two
baseline files under Scripts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8").resolve()
CONTRACT = PROJECT / "Scripts/cairnwell_2040_runtime_v001_import_contract.json"
CONTRACT_SHA = PROJECT / "Scripts/cairnwell_2040_runtime_v001_import_contract.sha256"
BASELINE = PROJECT / "Scripts/cairnwell_2040_runtime_v001_import_baseline.json"
BASELINE_SHA = PROJECT / "Scripts/cairnwell_2040_runtime_v001_import_baseline.sha256"
DEST_DISK = PROJECT / "Content/LineBoss/Factory/OneFactory/v001/Vehicles/Cairnwell2040Runtime_v001"
AUDIT_ROOT = PROJECT / "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/UnrealImportLane_v001"
ACK_TOKEN = "FREEZE_CAIRNWELL_2040_RUNTIME_V001_PROJECT_BASELINE_ONCE"
RESULT_NAMES = {
    "import_receipt_v001.json",
    "import_failure_v001.json",
    "fresh_process_validation_receipt_v001.json",
    "fresh_process_validation_failure_v001.json",
    "lane_summary_v001.json",
}


class BaselineError(RuntimeError):
    pass


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
        raise BaselineError(f"path escapes exact project root: {path}") from exc


def inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def file_row(path: Path) -> dict:
    if not path.is_file():
        raise BaselineError(f"required file missing: {path}")
    stat = path.stat()
    return {
        "path": relative(path),
        "bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": sha256(path),
    }


def canonical_hash(rows: list[dict]) -> str:
    compact = [
        {key: row[key] for key in ("path", "bytes", "mtime_ns", "sha256")}
        for row in sorted(rows, key=lambda item: item["path"].casefold())
    ]
    return hashlib.sha256(
        json.dumps(compact, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest().upper()


def inventory(paths: list[Path]) -> dict:
    rows = [file_row(path) for path in sorted(set(paths), key=lambda item: str(item).casefold())]
    return {"file_count": len(rows), "inventory_sha256": canonical_hash(rows), "files": rows}


def load_contract() -> tuple[dict, str]:
    if not CONTRACT.is_file() or not CONTRACT_SHA.is_file():
        raise BaselineError("approved final authority contract/sidecar intentionally absent")
    digest = sha256(CONTRACT)
    sidecar = CONTRACT_SHA.read_text(encoding="ascii").strip().split()[0].upper()
    if sidecar != digest:
        raise BaselineError("approved contract sidecar mismatch")
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    destination = payload.get("destination", {})
    provenance_raw = payload.get("provenance", {})
    provenance = provenance_raw if isinstance(provenance_raw, dict) else {}
    paint_mask_raw = payload.get("paint_mask_authority", {})
    paint_mask = paint_mask_raw if isinstance(paint_mask_raw, dict) else {}
    supersession_raw = payload.get("approval_supersession", {})
    supersession = supersession_raw if isinstance(supersession_raw, dict) else {}
    root_visual_raw = supersession.get("root_visual_approval", {})
    root_visual = root_visual_raw if isinstance(root_visual_raw, dict) else {}
    amendment_raw = supersession.get("freeze_amendment", {})
    amendment = amendment_raw if isinstance(amendment_raw, dict) else {}
    if (payload.get("$schema") != "lineboss/cairnwell-2040-runtime-v001/unreal-import-contract/v1"
            or payload.get("status")
            != "FROZEN__APPROVED_CAIRNWELL_V005_WINNER__READY_FOR_BASELINE"
            or destination.get("namespace")
            != "/Game/LineBoss/Factory/OneFactory/v001/Vehicles/Cairnwell2040Runtime_v001"
            or destination.get("expected_package_count") != 11
            or provenance.get("selected_candidate") != "ProductionCandidate_v005"
            or provenance.get("selected_version") != "v005"
            or provenance.get("manifest", {}).get("path") != (
                "SourceAssets/Candidate/Vehicles/Cairnwell2040/"
                "FinishedVehicleRuntimeDerivative_v001/ProductionCandidate_v005/"
                "MANIFEST_v005.json"
            )
            or paint_mask.get("status")
            != "APPROVED__MANUALLY_AUTHORED_V005_BODY_PAINT_MASK__VISUALLY_VALIDATED"
            or paint_mask.get("texture_semantic") != "metallic_roughness"
            or paint_mask.get("channel") != "A"
            or paint_mask.get("manual_authored") is not True
            or paint_mask.get("v006_mask_reused") is not False
            or int(paint_mask.get("false_positive_fragment_count", -1)) != 0
            or supersession.get("status") != (
                "APPROVED__V005_MANUAL_MASK_SUPERSEDES_HISTORICAL_"
                "DO_NOT_PROMOTE_WITHOUT_DELETION"
            )
            or supersession.get("historical_marker_preserved_byte_exact") is not True
            or supersession.get("supersedes_historical_marker_without_deletion") is not True
            or supersession.get("unreal_import_or_promotion_performed") is not False
            or root_visual.get("status") != "PASS"
            or int(root_visual.get("visible_isolated_false_positive_regions", -1)) != 0
            or amendment.get("schema")
            != "lineboss.cairnwell2040.v005.additive-freeze-amendment.v2"
            or amendment.get("status") != (
                "PASS__V005_ADDITIVE_FREEZE_RECEIPT_V002__CURRENT_CONTRACT_AUTHORITY__"
                "SOLE_SCHEMA_KEY_CORRECTION"
            )
            or amendment.get("current_contract_authority") is not True
            or amendment.get("supersedes_stale_v1_receipt_without_modifying_it") is not True
            or amendment.get("unreal_import_or_promotion_performed") is not False
            or amendment.get("record", {}).get("sha256")
            != "7BCE6A5A1DF2C0080011D8EB78D24C5839B44A4755F65FD2939F0E562D75A4A0"
            or amendment.get("stale_v1_receipt", {}).get("sha256")
            != "F7C761D794F44E7EEEBB2958A7947F63D59D0EE828510E1803D7B69EA62642F0"
            or amendment.get("current_supersession", {}).get("sha256")
            != "738E19C3D1D07028C0F2C107AD023F14DBC94FD44DAE2107411D6C8A317A348C"
            or amendment.get("no_missing_files") is not True
            or amendment.get("no_unexpected_additions") is not True
            or amendment.get("no_other_changed_files") is not True
            or payload.get("policy", {}).get("overwrite_reimport_delete_authorized") is not False):
        raise BaselineError("approved contract identity or safety policy drift")
    return payload, digest


def source_snapshot(contract: dict) -> dict:
    rows = []
    expected_paths = set()
    for expected in contract["provenance"]["source_files"]:
        path = PROJECT / expected["path"]
        actual = file_row(path)
        if actual["bytes"] != int(expected["bytes"]) or actual["sha256"] != expected["sha256"]:
            raise BaselineError(f"approved selected-authority input drift: {expected['path']}")
        rows.append(actual)
        expected_paths.add(expected["path"])
    if len(rows) != len(expected_paths):
        raise BaselineError("approved source inventory contains duplicate paths")
    return {
        "file_count": len(rows),
        "inventory_sha256": canonical_hash(rows),
        "files": sorted(rows, key=lambda row: row["path"].casefold()),
    }


def scan(root: Path, excludes: tuple[Path, ...] = ()) -> list[Path]:
    if not root.is_dir():
        return []
    return [
        path for path in root.rglob("*") if path.is_file()
        and not any(path.resolve() == excluded.resolve() or inside(path, excluded)
                    for excluded in excludes)
    ]


def protected_snapshot() -> dict:
    descriptor = PROJECT / "LineBossCarFactory.uproject"
    groups = [
        {
            "name": "project_descriptor",
            "roots": [],
            "files": [relative(descriptor)],
            "excludes": [],
            "allow_empty": False,
            "selected": [descriptor],
        },
        {
            "name": "complete_source_tree",
            "roots": ["Source"],
            "files": [],
            "excludes": [],
            "allow_empty": False,
            "selected": scan(PROJECT / "Source"),
        },
        {
            "name": "complete_config_tree",
            "roots": ["Config"],
            "files": [],
            "excludes": [],
            "allow_empty": False,
            "selected": scan(PROJECT / "Config"),
        },
        {
            "name": "all_existing_content_outside_destination_including_maps",
            "roots": ["Content"],
            "files": [],
            "excludes": [relative(DEST_DISK)],
            "allow_empty": False,
            "selected": scan(PROJECT / "Content", (DEST_DISK,)),
        },
        {
            "name": "campaign_save_games",
            "roots": ["Saved/SaveGames"],
            "files": [],
            "excludes": [],
            "allow_empty": True,
            "selected": scan(PROJECT / "Saved/SaveGames"),
        },
    ]
    union: dict[str, Path] = {}
    output_groups = []
    for group in groups:
        selected = group.pop("selected")
        if not selected and not group["allow_empty"]:
            raise BaselineError(f"protected group is unexpectedly empty: {group['name']}")
        paths = sorted({relative(path) for path in selected}, key=str.casefold)
        output_groups.append({**group, "paths": paths})
        for path in selected:
            union[relative(path)] = path
    snapshot = inventory(list(union.values()))
    snapshot["groups"] = output_groups
    return snapshot


def lane_snapshot(contract: dict) -> dict:
    paths = [CONTRACT, CONTRACT_SHA]
    paths.extend(PROJECT / rel for rel in contract["lane_files_to_pin_when_baseline_is_cut"])
    snapshot = inventory(paths)
    expected = {relative(path) for path in paths}
    actual = {row["path"] for row in snapshot["files"]}
    if actual != expected:
        raise BaselineError("prepared lane inventory drift")
    return snapshot


def prior_results() -> list[str]:
    if not AUDIT_ROOT.is_dir():
        return []
    return sorted(
        relative(path) for path in AUDIT_ROOT.rglob("*")
        if path.is_file() and path.name in RESULT_NAMES
    )


def create_baseline(acknowledgement: str) -> None:
    if acknowledgement != ACK_TOKEN:
        raise BaselineError("exact one-shot baseline acknowledgement missing")
    if BASELINE.exists() or BASELINE_SHA.exists():
        raise BaselineError("refusing to overwrite an existing Cairnwell baseline")
    if DEST_DISK.exists():
        raise BaselineError(f"fresh destination already exists: {DEST_DISK}")
    existing_results = prior_results()
    if existing_results:
        raise BaselineError("prior one-shot result exists: " + "; ".join(existing_results))
    contract, contract_digest = load_contract()
    payload = {
        "$schema": "lineboss/cairnwell-2040-runtime-v001/unreal-import-baseline/v1",
        "status": "FROZEN__CAIRNWELL_2040_RUNTIME_V001_PROJECT_BASELINE",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": str(PROJECT),
        "contract": {"path": relative(CONTRACT), "sha256": contract_digest},
        "destination": contract["destination"],
        "shared_datum": contract["shared_datum"],
        "import_contract": contract["import_contract"],
        "modules": contract["modules"],
        "textures": contract["textures"],
        "materials": contract["materials"],
        "paint_mask_authority": contract["paint_mask_authority"],
        "approval_supersession": contract["approval_supersession"],
        "source": source_snapshot(contract),
        "protected": protected_snapshot(),
        "lane": lane_snapshot(contract),
        "policy": contract["policy"],
    }
    BASELINE.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    digest = sha256(BASELINE)
    BASELINE_SHA.write_text(f"{digest}  {BASELINE.name}\n", encoding="ascii")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_PROJECT_BASELINE_FROZEN")
    print(digest)


def verify_snapshot(snapshot: dict, label: str) -> None:
    rows = [file_row(PROJECT / expected["path"]) for expected in snapshot["files"]]
    for expected, actual in zip(snapshot["files"], rows):
        if any(actual[key] != expected[key] for key in ("path", "bytes", "mtime_ns", "sha256")):
            raise BaselineError(f"{label} file drift: {expected['path']}")
    if len(rows) != int(snapshot["file_count"]) or canonical_hash(rows) != snapshot["inventory_sha256"]:
        raise BaselineError(f"{label} inventory drift")


def verify_protected_paths(snapshot: dict) -> None:
    for group in snapshot["groups"]:
        selected = {PROJECT / rel for rel in group.get("files", [])}
        for rel in group.get("roots", []):
            root = PROJECT / rel
            if root.is_dir():
                selected.update(path for path in root.rglob("*") if path.is_file())
            elif not group.get("allow_empty"):
                raise BaselineError(f"protected root missing: {rel}")
        exclusions = [PROJECT / rel for rel in group.get("excludes", [])]
        selected = {
            path for path in selected
            if not any(path.resolve() == excluded.resolve() or inside(path, excluded)
                       for excluded in exclusions)
        }
        if {relative(path) for path in selected} != set(group["paths"]):
            raise BaselineError(f"protected path inventory drift: {group['name']}")


def load_frozen_baseline() -> tuple[dict, str]:
    contract, contract_digest = load_contract()
    if not BASELINE.is_file() or not BASELINE_SHA.is_file():
        raise BaselineError("baseline intentionally absent pending final contract freeze")
    digest = sha256(BASELINE)
    if BASELINE_SHA.read_text(encoding="ascii").strip().split()[0].upper() != digest:
        raise BaselineError("baseline sidecar mismatch")
    payload = json.loads(BASELINE.read_text(encoding="utf-8"))
    if (payload.get("$schema") != "lineboss/cairnwell-2040-runtime-v001/unreal-import-baseline/v1"
            or payload.get("status") != "FROZEN__CAIRNWELL_2040_RUNTIME_V001_PROJECT_BASELINE"
            or payload.get("contract", {}).get("sha256") != contract_digest
            or payload.get("destination") != contract.get("destination")
            or payload.get("shared_datum") != contract.get("shared_datum")
            or payload.get("import_contract") != contract.get("import_contract")
            or payload.get("modules") != contract.get("modules")
            or payload.get("textures") != contract.get("textures")
            or payload.get("materials") != contract.get("materials")
            or payload.get("paint_mask_authority") != contract.get("paint_mask_authority")
            or payload.get("approval_supersession") != contract.get("approval_supersession")
            or payload.get("policy") != contract.get("policy")):
        raise BaselineError("baseline identity/contract drift")
    return payload, digest


def verify_immutable_snapshots(payload: dict) -> None:
    verify_snapshot(payload["source"], "approved source")
    verify_protected_paths(payload["protected"])
    verify_snapshot(payload["protected"], "protected project")
    verify_snapshot(payload["lane"], "prepared lane")


def verify_baseline() -> None:
    payload, digest = load_frozen_baseline()
    verify_immutable_snapshots(payload)
    if DEST_DISK.exists() or prior_results():
        raise BaselineError("baseline pre-import freshness drift")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_FULL_BASELINE_REVERIFIED")
    print(digest)


def verify_post_import_immutable() -> None:
    payload, digest = load_frozen_baseline()
    verify_immutable_snapshots(payload)
    print(
        "PASS__CAIRNWELL_2040_RUNTIME_V001_POST_IMPORT_SOURCE_PROTECTED_LANE_REVERIFIED"
    )
    print(digest)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--acknowledgement", default="")
    verification = parser.add_mutually_exclusive_group()
    verification.add_argument("--verify-only", action="store_true")
    verification.add_argument("--verify-post-import-immutable", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        verify_baseline()
    elif args.verify_post_import_immutable:
        verify_post_import_immutable()
    else:
        create_baseline(args.acknowledgement)


if __name__ == "__main__":
    main()
