"""Freeze or verify the incident-bound Cairnwell runtime recovery v002.

Standard-library only.  This tool never launches Unreal, moves/deletes files,
or writes outside the recovery contract and its SHA-256 sidecar.
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
OUTPUT = PROJECT / "Scripts/cairnwell_2040_runtime_v001_recovery_v002_contract.json"
OUTPUT_SHA = PROJECT / "Scripts/cairnwell_2040_runtime_v001_recovery_v002_contract.sha256"
DEST = PROJECT / "Content/LineBoss/Factory/OneFactory/v001/Vehicles/Cairnwell2040Runtime_v001"
AUDIT_ROOT = PROJECT / "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/UnrealImportLane_v001"
FAILED_RUN_ID = "20260815T094919Z-7dfb3c0a"
FAILED_RUN = AUDIT_ROOT / FAILED_RUN_ID
RECOVERY_AUDIT_ROOT = AUDIT_ROOT / "Recovery_v002"
QUARANTINE = (
    PROJECT / "Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
    "Incident_20260815T094919Z-7dfb3c0a_v001"
)
ACK_TOKEN = "FREEZE_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V002_ONCE"
RUN_ACK_TOKEN = "RECOVER_QUARANTINED_CAIRNWELL_2040_RUNTIME_V001_V002_ONCE"
STATUS = (
    "FROZEN__CAIRNWELL_2040_RUNTIME_V001_INCIDENT_BOUND_RECOVERY_V002__"
    "READY_FOR_ONE_SHOT_QUARANTINE_AND_TWO_PROCESS_IMPORT"
)
CONTRACT_EXPECTED_SHA256 = "B0D276A85E8532B580098092384BD93D0E5F55E3A437922FFFC31D69B8816EB1"
BASELINE_EXPECTED_SHA256 = "493CEBCA0DAA09179D0F44BE2FE4E4D60658D8F42CD88A02268045591EE77882"
FAILED_FILES = {
    "import_failure_v001.json": (4288, "05F204CDE09BD22BED823101525C82F64E18F8EE56BC6004C9E0979AA73CFC2D"),
    "lane_summary_v001.json": (1771, "00DA69AEA08322AFFD099D5126BADA3F78265EDC9A38302D3C3CC2B3D118CEA5"),
    "unreal_import.log": (344784, "11AADD66D2C685202B1C07C9E1A2E493CEC7C796398FD8AE59A2AE4569CDA367"),
    "unreal_import.stderr.log": (0, "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"),
    "unreal_import.stdout.log": (344814, "5F173EEFEB82A3A6930B062CB8755AD7617C2F9B8851CE7782085A223E1DF8A2"),
}
PARTIAL_HASHES = {
    "Materials/M_LB_C2040_BIWGalvanized_v001.uasset": (
        6002, 1786787454166374600,
        "FCE1DDBA01C45F7162297F6C5D048394F8FA5CCD01E43851044D517FDA1739D9"),
    "Textures/T_LB_C2040_Emerald_BaseColor_v001.uasset": (
        3818680, 1786787453931382900,
        "D057B1C2A56F8F17CD0ED77321FD803EC733FA8E845504D34D52CA99F4180CFD"),
    "Textures/T_LB_C2040_Emerald_MRBodyMask_v001.uasset": (
        5818244, 1786787453981375100,
        "F4ADBF3AC8E0ACE8D053D6BD3E73EA887EC3FF33C63CDF0F61FBC767DE400309"),
    "Textures/T_LB_C2040_Emerald_Normal_v001.uasset": (
        3973188, 1786787454019375700,
        "67465B09C9B5418F08EDE7E2195E297472AE35E0BA96A05545EB0FE179CBEB7A"),
}
ORIGINAL_LANE_CHANGED = {
    "Scripts/cairnwell_2040_runtime_v001.py",
    "Scripts/import_cairnwell_2040_runtime_v001.py",
    "Scripts/validate_cairnwell_2040_runtime_fresh_process_v001.py",
    "Scripts/run_cairnwell_2040_runtime_import_lane_v001.ps1",
    "Scripts/tests/test_cairnwell_2040_runtime_import_lane_v001.py",
}
RECOVERY_LANE_PATHS = {
    "Docs/OneFactory/CAIRNWELL_2040_RUNTIME_V001_UNREAL_IMPORT_LANE.md",
    "Docs/OneFactory/CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V002.md",
    "Scripts/cairnwell_2040_runtime_v001.py",
    "Scripts/cairnwell_2040_runtime_v001_import_contract.json",
    "Scripts/cairnwell_2040_runtime_v001_import_contract.sha256",
    "Scripts/cairnwell_2040_runtime_v001_import_baseline.json",
    "Scripts/cairnwell_2040_runtime_v001_import_baseline.sha256",
    "Scripts/import_cairnwell_2040_runtime_v001.py",
    "Scripts/prepare_cairnwell_2040_runtime_v001_baseline.py",
    "Scripts/prepare_cairnwell_2040_runtime_v001_contract.py",
    "Scripts/prepare_cairnwell_2040_runtime_v001_recovery_v002.py",
    "Scripts/run_cairnwell_2040_runtime_import_lane_v001.ps1",
    "Scripts/tests/test_cairnwell_2040_runtime_import_lane_v001.py",
    "Scripts/validate_cairnwell_2040_runtime_fresh_process_v001.py",
}
OLD_PASS_NAMES = {
    "import_receipt_v001.json",
    "fresh_process_validation_receipt_v001.json",
}


class RecoveryError(RuntimeError):
    pass


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
        raise RecoveryError(f"path escapes exact project root: {path}") from exc


def file_row(path: Path) -> dict:
    if not path.is_file():
        raise RecoveryError(f"required file missing: {path}")
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


def object_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest().upper()


def inventory(paths: list[Path]) -> dict:
    rows = [file_row(path) for path in sorted(set(paths), key=lambda item: str(item).casefold())]
    return {"file_count": len(rows), "inventory_sha256": canonical_hash(rows), "files": rows}


def exact_sidecar(payload: Path, sidecar: Path, expected: str, label: str) -> str:
    digest = sha256(payload)
    if digest != expected:
        raise RecoveryError(f"{label} hash drift: {digest}")
    if sidecar.read_text(encoding="ascii").strip().split()[0].upper() != digest:
        raise RecoveryError(f"{label} sidecar drift")
    return digest


def verify_snapshot(snapshot: dict, label: str) -> None:
    rows = []
    for expected in snapshot.get("files", []):
        actual = file_row(PROJECT / expected["path"])
        if actual != expected:
            raise RecoveryError(f"{label} file drift: {expected['path']}")
        rows.append(actual)
    if (len(rows) != int(snapshot.get("file_count", -1))
            or canonical_hash(rows) != snapshot.get("inventory_sha256")):
        raise RecoveryError(f"{label} inventory drift")


def verify_protected_paths(snapshot: dict) -> None:
    for group in snapshot["groups"]:
        selected = {PROJECT / rel for rel in group.get("files", [])}
        for rel in group.get("roots", []):
            root = PROJECT / rel
            if root.is_dir():
                selected.update(path for path in root.rglob("*") if path.is_file())
            elif not group.get("allow_empty"):
                raise RecoveryError("protected root missing: " + rel)
        exclusions = [PROJECT / rel for rel in group.get("excludes", [])]
        selected = {
            path for path in selected
            if not any(path.resolve() == excluded.resolve() or inside(path, excluded)
                       for excluded in exclusions)
        }
        if {relative(path) for path in selected} != set(group["paths"]):
            raise RecoveryError("protected path inventory drift: " + group["name"])


def load_original() -> tuple[dict, str, str]:
    contract_digest = exact_sidecar(
        CONTRACT, CONTRACT_SHA, CONTRACT_EXPECTED_SHA256, "original frozen contract")
    baseline_digest = exact_sidecar(
        BASELINE, BASELINE_SHA, BASELINE_EXPECTED_SHA256, "original frozen baseline")
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    if (baseline.get("status") != "FROZEN__CAIRNWELL_2040_RUNTIME_V001_PROJECT_BASELINE"
            or baseline.get("contract", {}).get("sha256") != contract_digest):
        raise RecoveryError("original frozen baseline identity drift")
    verify_snapshot(baseline["source"], "approved v005 source authority")
    verify_protected_paths(baseline["protected"])
    verify_snapshot(baseline["protected"], "protected project")
    return baseline, contract_digest, baseline_digest


def verify_original_lane_drift(baseline: dict) -> None:
    changed = set()
    for expected in baseline["lane"]["files"]:
        actual = file_row(PROJECT / expected["path"])
        if actual != expected:
            changed.add(expected["path"])
    if changed != ORIGINAL_LANE_CHANGED:
        raise RecoveryError(
            "original prepared-lane drift is not the exact recovery patch set: "
            + repr(sorted(changed)))


def recovery_lane_snapshot() -> dict:
    snapshot = inventory([PROJECT / rel for rel in RECOVERY_LANE_PATHS])
    if {row["path"] for row in snapshot["files"]} != RECOVERY_LANE_PATHS:
        raise RecoveryError("recovery v002 lane path closure drift")
    return snapshot


def incident_rows() -> dict[str, dict]:
    if not FAILED_RUN.is_dir():
        raise RecoveryError("exact failed v001 run is absent")
    actual_names = {path.name for path in FAILED_RUN.iterdir() if path.is_file()}
    if actual_names != set(FAILED_FILES):
        raise RecoveryError("failed v001 run file closure drift: " + repr(sorted(actual_names)))
    rows = {}
    for name, (expected_bytes, expected_hash) in FAILED_FILES.items():
        row = file_row(FAILED_RUN / name)
        if row["bytes"] != expected_bytes or row["sha256"] != expected_hash:
            raise RecoveryError("failed v001 evidence hash drift: " + name)
        rows[name] = row
    failure = json.loads((FAILED_RUN / "import_failure_v001.json").read_text(encoding="utf-8"))
    summary = json.loads((FAILED_RUN / "lane_summary_v001.json").read_text(encoding="utf-8"))
    if (failure.get("$schema") != "lineboss/audit/cairnwell-2040-runtime-v001/unreal-import/v1"
            or failure.get("status") != "FAIL_CLOSED__CAIRNWELL_2040_RUNTIME_V001_UNREAL_IMPORT"
            or failure.get("error") != (
                "CAIRNWELL_2040_RUNTIME_V001_UNREAL_LANE_FAIL: material expression "
                "connection failed: body:normalized_detail_to_clamp")
            or summary.get("status")
            != "FAIL_CLOSED__CAIRNWELL_2040_RUNTIME_V001_UNREAL_IMPORT_LANE"
            or int(summary.get("import_process", {}).get("exit_code", 0)) != 3):
        raise RecoveryError("failed v001 incident identity/root-cause drift")
    old_passes = [
        relative(path) for path in AUDIT_ROOT.rglob("*")
        if path.is_file() and path.name in OLD_PASS_NAMES
    ]
    if old_passes:
        raise RecoveryError("old v001 PASS receipt unexpectedly exists: " + repr(old_passes))
    return rows


def partial_rows(root: Path, expected_location: str) -> dict[str, dict]:
    if not root.is_dir():
        raise RecoveryError(expected_location + " partial-package root is absent")
    actual = {path.relative_to(root).as_posix(): path for path in root.rglob("*") if path.is_file()}
    if set(actual) != set(PARTIAL_HASHES):
        raise RecoveryError(expected_location + " partial-package closure drift")
    rows = {}
    for rel, (expected_bytes, expected_mtime, expected_hash) in PARTIAL_HASHES.items():
        row = file_row(actual[rel])
        if (row["bytes"] != expected_bytes or row["mtime_ns"] != expected_mtime
                or row["sha256"] != expected_hash):
            raise RecoveryError(expected_location + " partial-package hash/mtime drift: " + rel)
        rows[rel] = row
    return rows


def partial_contract_rows() -> dict[str, dict]:
    current = partial_rows(DEST, "source destination")
    failure = json.loads((FAILED_RUN / "import_failure_v001.json").read_text(encoding="utf-8"))
    preserved = failure.get("namespace_files_preserved_for_recovery", {})
    output = {}
    for rel, row in current.items():
        source_path = relative(DEST / rel)
        pinned = preserved.get(source_path)
        if (not isinstance(pinned, dict)
                or any(pinned.get(key) != row[key] for key in ("bytes", "mtime_ns", "sha256"))):
            raise RecoveryError("failed receipt does not pin exact partial: " + source_path)
        output[source_path] = {
            "source_path": source_path,
            "quarantine_path": relative(QUARANTINE / rel),
            "bytes": row["bytes"],
            "mtime_ns": row["mtime_ns"],
            "sha256": row["sha256"],
        }
    return output


def incident_binding(rows: dict[str, dict], partials: dict[str, dict]) -> dict:
    binding = {
        "failed_run_id": FAILED_RUN_ID,
        "import_failure": rows["import_failure_v001.json"],
        "lane_summary": rows["lane_summary_v001.json"],
        "partial_package_sha256": {
            path: row["sha256"] for path, row in sorted(partials.items())
        },
        "old_v001_pass_receipts_present": False,
    }
    binding["binding_sha256"] = object_hash(binding)
    return binding


def result_topology() -> dict:
    return {
        "audit_root": relative(RECOVERY_AUDIT_ROOT),
        "run_root_pattern": relative(RECOVERY_AUDIT_ROOT) + "/<UTC>-<GUID8>",
        "quarantine_receipt": {
            "filename": "quarantine_receipt_v002.json",
            "$schema": "lineboss/audit/cairnwell-2040-runtime-v001/recovery-v002/quarantine/v2",
            "pass_status": "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V002_PARTIALS_QUARANTINED",
        },
        "import": {
            "receipt_filename": "import_receipt_recovery_v002.json",
            "failure_filename": "import_failure_recovery_v002.json",
            "$schema": "lineboss/audit/cairnwell-2040-runtime-v001/recovery-v002/unreal-import/v2",
            "pass_status": (
                "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V002_FRESH_IMPORT__4_MESHES__"
                "12_AUTHORED_LODS__3_TEXTURES__4_MATERIALS__EXACT_11_PACKAGE_CLOSURE"),
            "package_hash_field": "package_sha256",
        },
        "fresh_validation": {
            "receipt_filename": "fresh_process_validation_receipt_recovery_v002.json",
            "failure_filename": "fresh_process_validation_failure_recovery_v002.json",
            "$schema": (
                "lineboss/audit/cairnwell-2040-runtime-v001/"
                "recovery-v002/fresh-process-validation/v2"),
            "pass_status": (
                "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V002_DISTINCT_FRESH_PROCESS__"
                "READ_ONLY_RELOAD__11_PACKAGE_HASHES_UNCHANGED"),
            "package_hash_fields": ["package_sha256_before_loads", "package_sha256_after_loads"],
        },
        "summary": {
            "filename": "lane_summary_recovery_v002.json",
            "$schema": "lineboss/audit/cairnwell-2040-runtime-v001/recovery-v002/import-lane-summary/v2",
            "pass_status": (
                "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V002_GUARDED_IMPORT_AND_"
                "DISTINCT_READ_ONLY_RELOAD"),
        },
        "required_incident_binding_fields": [
            "recovery_contract_sha256", "failed_run_id",
            "failed_import_failure_sha256", "incident_binding_sha256",
            "quarantine_receipt",
        ],
    }


def create_contract(acknowledgement: str) -> None:
    if acknowledgement != ACK_TOKEN:
        raise RecoveryError("exact one-shot recovery-freeze acknowledgement missing")
    if OUTPUT.exists() or OUTPUT_SHA.exists():
        raise RecoveryError("refusing to overwrite an existing recovery contract or sidecar")
    if RECOVERY_AUDIT_ROOT.exists() or QUARANTINE.exists():
        raise RecoveryError("recovery result/quarantine already exists; v002 cannot be frozen")
    baseline, contract_digest, baseline_digest = load_original()
    verify_original_lane_drift(baseline)
    incident = incident_rows()
    partials = partial_contract_rows()
    binding = incident_binding(incident, partials)
    payload = {
        "$schema": "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v2",
        "status": STATUS,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "acknowledgement": RUN_ACK_TOKEN,
        "project_root": str(PROJECT),
        "original_authorities": {
            "contract": file_row(CONTRACT),
            "contract_sidecar": file_row(CONTRACT_SHA),
            "baseline": file_row(BASELINE),
            "baseline_sidecar": file_row(BASELINE_SHA),
        },
        "approved_source": {
            "file_count": baseline["source"]["file_count"],
            "inventory_sha256": baseline["source"]["inventory_sha256"],
        },
        "protected_project": {
            "file_count": baseline["protected"]["file_count"],
            "inventory_sha256": baseline["protected"]["inventory_sha256"],
        },
        "original_lane": {
            "file_count": baseline["lane"]["file_count"],
            "inventory_sha256": baseline["lane"]["inventory_sha256"],
            "exact_changed_files": sorted(ORIGINAL_LANE_CHANGED, key=str.casefold),
        },
        "lane": recovery_lane_snapshot(),
        "incident": {
            **binding,
            "root": relative(FAILED_RUN),
            "files": incident,
            "primary_failure": "normalized_luminance -> detail_clamp semantic Input",
            "ue58_pin_contract": (
                "UMaterialGraphNode::GetShortenPinName maps MaterialPinNames::Input to "
                "NAME_None; MaterialEditingLibrary therefore requires empty ToInputName."),
            "secondary_shutdown_failure": (
                "Explicit same-frame quit_editor was removed; ExecutePythonScript owns its "
                "deferred QUIT_EDITOR next-tick lifecycle."),
        },
        "partial_packages": partials,
        "quarantine": {
            "source_root": relative(DEST),
            "destination_root": relative(QUARANTINE),
            "operation": "MOVE_DIRECTORY_ONLY__NO_DELETE",
            "automatic_delete_authorized": False,
            "rerun_after_any_recovery_result_authorized": False,
        },
        "result_topology": result_topology(),
        "policy": {
            "unreal_launch_authorized_by_freeze": False,
            "source_config_maps_saves_writes_authorized": False,
            "map_load_save_authorized": False,
            "runtime_binding_or_promotion_authorized": False,
            "panel_module_namespace_or_packages_authorized": False,
            "quarantine_move_requires_explicit_guarded_runner_acknowledgement": True,
            "strict_editor_exit_code_zero_required": True,
            "post_receipt_fatal_or_crash_accepted": False,
        },
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    digest = sha256(OUTPUT)
    OUTPUT_SHA.write_text(f"{digest}  {OUTPUT.name}\n", encoding="ascii")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V002_CONTRACT_FROZEN")
    print(digest)


def load_frozen() -> tuple[dict, dict]:
    baseline, contract_digest, baseline_digest = load_original()
    digest = sha256(OUTPUT)
    if OUTPUT_SHA.read_text(encoding="ascii").strip().split()[0].upper() != digest:
        raise RecoveryError("recovery v002 contract sidecar drift")
    payload = json.loads(OUTPUT.read_text(encoding="utf-8"))
    original = payload.get("original_authorities", {})
    incident = payload.get("incident", {})
    if (payload.get("$schema") != "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v2"
            or payload.get("status") != STATUS
            or payload.get("acknowledgement") != RUN_ACK_TOKEN
            or original.get("contract", {}).get("sha256") != contract_digest
            or original.get("baseline", {}).get("sha256") != baseline_digest
            or incident.get("failed_run_id") != FAILED_RUN_ID
            or incident.get("import_failure", {}).get("sha256") != FAILED_FILES["import_failure_v001.json"][1]
            or payload.get("quarantine", {}).get("operation") != "MOVE_DIRECTORY_ONLY__NO_DELETE"
            or payload.get("policy", {}).get("unreal_launch_authorized_by_freeze") is not False):
        raise RecoveryError("recovery v002 contract identity/safety drift")
    for key in ("contract", "contract_sidecar", "baseline", "baseline_sidecar"):
        if file_row(PROJECT / original[key]["path"]) != original[key]:
            raise RecoveryError("original frozen authority row drift: " + key)
    verify_original_lane_drift(baseline)
    verify_snapshot(payload["lane"], "prepared recovery v002 lane")
    current_incident = incident_rows()
    if current_incident != incident.get("files"):
        raise RecoveryError("preserved failed incident row drift")
    return payload, baseline


def verify_partial_contract(payload: dict, location: str) -> None:
    root = DEST if location == "source destination" else QUARANTINE
    rows = partial_rows(root, location)
    for rel, actual in rows.items():
        source_path = relative(DEST / rel)
        expected = payload["partial_packages"].get(source_path, {})
        expected_path = source_path if location == "source destination" else expected.get("quarantine_path")
        if (actual["path"] != expected_path
                or any(actual[key] != expected.get(key)
                       for key in ("bytes", "mtime_ns", "sha256"))):
            raise RecoveryError(location + " does not match frozen partial contract: " + rel)


def verify_pre_quarantine() -> None:
    payload, _ = load_frozen()
    if QUARANTINE.exists() or RECOVERY_AUDIT_ROOT.exists():
        raise RecoveryError("recovery v002 quarantine/result already exists")
    verify_partial_contract(payload, "source destination")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V002_PRE_QUARANTINE_REVERIFIED")
    print(sha256(OUTPUT))


def verify_post_quarantine() -> None:
    payload, _ = load_frozen()
    if DEST.exists():
        raise RecoveryError("fresh destination still exists after quarantine move")
    verify_partial_contract(payload, "quarantine")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V002_POST_QUARANTINE_REVERIFIED")
    print(sha256(OUTPUT))


def verify_post_import() -> None:
    payload, baseline = load_frozen()
    verify_partial_contract(payload, "quarantine")
    expected = set(baseline["destination"]["expected_package_paths"])
    actual = {
        "/Game/" + path.relative_to(PROJECT / "Content").with_suffix("").as_posix()
        for path in DEST.rglob("*.uasset")
    } if DEST.is_dir() else set()
    if actual != expected or len(actual) != 11:
        raise RecoveryError("post-import destination is not the exact eleven-package closure")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V002_POST_IMPORT_REVERIFIED")
    print(sha256(OUTPUT))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--acknowledgement", default="")
    verification = parser.add_mutually_exclusive_group()
    verification.add_argument("--verify-pre-quarantine", action="store_true")
    verification.add_argument("--verify-post-quarantine", action="store_true")
    verification.add_argument("--verify-post-import", action="store_true")
    args = parser.parse_args()
    if args.verify_pre_quarantine:
        verify_pre_quarantine()
    elif args.verify_post_quarantine:
        verify_post_quarantine()
    elif args.verify_post_import:
        verify_post_import()
    else:
        create_contract(args.acknowledgement)


if __name__ == "__main__":
    main()
