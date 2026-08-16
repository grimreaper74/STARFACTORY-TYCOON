"""Offline whole-project baseline freezer for the guarded vehicle-WIP UE lane.

DO NOT run the creation mode until the shared OneFactory Paint integration and
combined build have settled. This file is prepared now, but no baseline is cut by
this task. It imports no Unreal module and starts no process.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8").resolve()
CONTRACT = PROJECT / "Scripts/vehicle_wip_native_kit_unreal_import_contract_v001.json"
EXPECTED_CONTRACT_SHA256 = "87D9FD32964CC0AD0F4AA52CC6F27A0E23BFDA23A18B2F714E6E2807CCA9684D"
BASELINE = PROJECT / "Scripts/vehicle_wip_native_kit_unreal_import_baseline_v001.json"
BASELINE_SHA = PROJECT / "Scripts/vehicle_wip_native_kit_unreal_import_baseline_v001.sha256"
DEST_DISK = PROJECT / "Content/LineBoss/Native/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001"
AUDIT_ROOT = PROJECT / "Saved/Audits/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001/UnrealImportLane_v001"
ACK_TOKEN = "FREEZE_VEHICLE_WIP_NATIVE_PROJECT_BASELINE_AFTER_PAINT_SETTLES_V001"
RESULT_NAMES = {
    "import_receipt_v001.json", "import_failure_v001.json",
    "fresh_load_validation_receipt_v001.json", "fresh_load_validation_failure_v001.json",
    "lane_summary_v001.json",
}


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest().upper()


def relative(path: Path) -> str:
    return path.resolve().relative_to(PROJECT).as_posix()


def inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def file_row(path: Path) -> dict:
    if not path.is_file():
        raise RuntimeError("required file missing: " + str(path))
    stat = path.stat()
    return {"path": relative(path), "bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns, "sha256": sha256(path)}


def canonical_hash(rows: list[dict]) -> str:
    compact = [{key: row[key] for key in ("path", "bytes", "mtime_ns", "sha256")}
               for row in sorted(rows, key=lambda item: item["path"].casefold())]
    return hashlib.sha256(json.dumps(compact, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest().upper()


def load_contract() -> dict:
    if not CONTRACT.is_file() or sha256(CONTRACT) != EXPECTED_CONTRACT_SHA256:
        raise RuntimeError("static source contract absent or hash changed")
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if (payload.get("$schema") != "lineboss/vehicle-wip-native-kit-v001/unreal-static-import-contract/v1"
            or payload.get("status") != "READY__STATIC_SOURCE_CONTRACT_ONLY__WAITING_FOR_SHARED_PROJECT_BASELINE"
            or payload.get("destination", {}).get("expected_asset_count") != 16
            or payload.get("destination", {}).get("expected_lod_count_per_asset") != 3
            or payload.get("policy", {}).get("overwrite_reimport_delete_authorized") is not False):
        raise RuntimeError("static source contract identity/safety drift")
    return payload


def verify_frozen_source(contract: dict) -> dict:
    root = PROJECT / contract["source"]["root"]
    frozen_path = PROJECT / contract["source"]["frozen_receipt"]["path"]
    frozen_sha_path = PROJECT / contract["source"]["frozen_sidecar"]["path"]
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    if sha256(frozen_path) != contract["source"]["frozen_receipt"]["sha256"]:
        raise RuntimeError("frozen receipt hash drift")
    if sha256(frozen_sha_path) != contract["source"]["frozen_sidecar"]["sha256"]:
        raise RuntimeError("frozen sidecar hash drift")
    if frozen_sha_path.read_text(encoding="utf-8").strip().split()[0].upper() != sha256(frozen_path):
        raise RuntimeError("frozen receipt sidecar mismatch")
    wanted = {entry["path"]: entry for entry in frozen["files"]}
    for rel, expected in wanted.items():
        path = root / rel
        if not path.is_file() or path.stat().st_size != int(expected["bytes"]) or sha256(path) != expected["sha256"]:
            raise RuntimeError("frozen source file drift: " + rel)
    actual_rel = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
    expected_rel = set(wanted) | {frozen_path.relative_to(root).as_posix(), frozen_sha_path.relative_to(root).as_posix()}
    if actual_rel != expected_rel:
        raise RuntimeError("frozen source path inventory drift")
    rows = [file_row(root / rel) for rel in sorted(actual_rel, key=str.casefold)]
    for key, spec in contract["assets"].items():
        for lod in spec["lods"]:
            source = PROJECT / lod["source"]
            if sha256(source) != lod["source_sha256"] or source.stat().st_size != lod["source_bytes"]:
                raise RuntimeError(f"contract FBX drift: {key}:LOD{lod['lod']}")
    return {"root": contract["source"]["root"], "file_count": len(rows),
            "inventory_sha256": canonical_hash(rows), "all_files": rows}


def scan_files(root: Path, excludes=()) -> list[Path]:
    if not root.is_dir():
        return []
    output = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(path.resolve() == ex.resolve() or inside(path, ex) for ex in excludes):
            continue
        output.append(path)
    return sorted(output, key=lambda item: str(item).casefold())


def protected_snapshot() -> dict:
    descriptor = PROJECT / "LineBossCarFactory.uproject"
    if not descriptor.is_file():
        raise RuntimeError("project descriptor missing")
    groups = [
        {"name": "project_descriptor", "files": [relative(descriptor)], "roots": [], "excludes": [],
         "allow_empty": False, "selected": [descriptor]},
        {"name": "complete_source_tree", "files": [], "roots": ["Source"], "excludes": [],
         "allow_empty": False, "selected": scan_files(PROJECT / "Source")},
        {"name": "complete_config_tree", "files": [], "roots": ["Config"], "excludes": [],
         "allow_empty": False, "selected": scan_files(PROJECT / "Config")},
        {"name": "campaign_save_games", "files": [], "roots": ["Saved/SaveGames"], "excludes": [],
         "allow_empty": True, "selected": scan_files(PROJECT / "Saved/SaveGames")},
        {"name": "all_existing_content_outside_new_native_namespace", "files": [], "roots": ["Content"],
         "excludes": [relative(DEST_DISK)], "allow_empty": False,
         "selected": scan_files(PROJECT / "Content", excludes=(DEST_DISK,))},
    ]
    union: dict[str, Path] = {}
    group_rows = []
    for group in groups:
        name, paths = group["name"], group.pop("selected")
        rels = []
        for path in paths:
            rel = relative(path)
            union[rel] = path
            rels.append(rel)
        group["file_count"] = len(rels)
        group["paths"] = sorted(rels, key=str.casefold)
        group_rows.append(group)
    rows = [file_row(union[rel]) for rel in sorted(union, key=str.casefold)]
    maps = {row["path"]: row for row in rows if row["path"].lower().endswith(".umap")}
    return {"file_count": len(rows), "inventory_sha256": canonical_hash(rows),
            "groups": group_rows, "files": rows, "maps": maps}


def lane_snapshot(contract: dict) -> dict:
    rows = []
    for rel in contract["lane_files_to_pin_when_baseline_is_cut"]:
        path = PROJECT / rel
        if not path.is_file():
            raise RuntimeError("prepared lane file missing when baseline cut: " + rel)
        rows.append(file_row(path))
    return {"file_count": len(rows), "inventory_sha256": canonical_hash(rows), "files": rows}


def prior_results() -> list[str]:
    if not AUDIT_ROOT.is_dir():
        return []
    return sorted(relative(path) for path in AUDIT_ROOT.rglob("*") if path.is_file() and path.name in RESULT_NAMES)


def create_baseline(acknowledgement: str) -> None:
    if acknowledgement != ACK_TOKEN:
        raise RuntimeError("exact post-Paint baseline acknowledgement absent")
    if BASELINE.exists() or BASELINE_SHA.exists():
        raise RuntimeError("refusing to overwrite existing vehicle-WIP baseline")
    if DEST_DISK.exists():
        raise RuntimeError("fresh target namespace already exists")
    if prior_results():
        raise RuntimeError("one-shot lane results already exist")
    contract = load_contract()
    source = verify_frozen_source(contract)
    protected = protected_snapshot()
    lane = lane_snapshot(contract)
    payload = {
        "$schema": "lineboss/vehicle-wip-native-kit-v001/unreal-import-baseline/v1",
        "status": "FROZEN__VEHICLE_WIP_NATIVE_KIT_V001_UNREAL_IMPORT_BASELINE_V001",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "acknowledgement": acknowledgement,
        "contract": {"path": relative(CONTRACT), "sha256": sha256(CONTRACT)},
        "source": source,
        "lane": lane,
        "protected": protected,
        "destination": contract["destination"],
        "import_contract": contract["import_contract"],
        "assets": contract["assets"],
        "policy": contract["policy"],
    }
    BASELINE.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    BASELINE_SHA.write_text(f"{sha256(BASELINE)}  {relative(BASELINE)}\n", encoding="utf-8")
    print("PASS__FULL_SOURCE_CONTENT_CONFIG_MAP_SAVE_BASELINE_FROZEN_AFTER_PAINT_SETTLED")
    print(sha256(BASELINE))


def verify_baseline() -> None:
    if not BASELINE.is_file() or not BASELINE_SHA.is_file():
        raise RuntimeError("baseline/sidecar absent; this is expected before Paint settles")
    if BASELINE_SHA.read_text(encoding="utf-8").strip().split()[0].upper() != sha256(BASELINE):
        raise RuntimeError("baseline sidecar mismatch")
    contract = load_contract()
    payload = json.loads(BASELINE.read_text(encoding="utf-8"))
    if payload.get("status") != "FROZEN__VEHICLE_WIP_NATIVE_KIT_V001_UNREAL_IMPORT_BASELINE_V001":
        raise RuntimeError("baseline status drift")
    if payload["contract"]["sha256"] != sha256(CONTRACT):
        raise RuntimeError("baseline contract drift")
    current_source = verify_frozen_source(contract)
    current_protected = protected_snapshot()
    current_lane = lane_snapshot(contract)
    for label, current in (("source", current_source), ("protected", current_protected), ("lane", current_lane)):
        if (current["file_count"] != payload[label]["file_count"]
                or current["inventory_sha256"] != payload[label]["inventory_sha256"]):
            raise RuntimeError(label + " baseline reverify drift")
    print("PASS__FULL_SOURCE_AND_PROTECTED_BASELINE_REVERIFY")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--acknowledgement", default="")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        verify_baseline()
    else:
        create_baseline(args.acknowledgement)


if __name__ == "__main__":
    main()
