"""Archive two failed runs and atomically relocate the invalid v001 namespace.

Offline CPython only.  Every source is hash-checked, exclusively copied, checked
again, then made read-only.  Only after both failed runs and all eight packages
are preserved does one same-volume directory rename move the invalid Content
namespace into Saved/Audits.  Nothing is deleted or overwritten.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import traceback
from datetime import datetime, timezone
from pathlib import Path


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8").resolve()
CONTRACT = PROJECT / "Scripts/body_shop_robot_native_unreal_recovery_contract_v001.json"
EXPECTED_CONTRACT_SHA256 = "E9862B44C656586879EF3607C33BD8A536E9CE0D816C144AFF870C31A7B52BC3"
AUDIT_ROOT = PROJECT / "Saved/Audits/BodyShop/RobotNative_v001/UnrealImportLane"
DESTINATION = PROJECT / "Content/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001"
RUN_ROOT_ENV = "LINEBOSS_BS_ROBOT_NATIVE_RUN_ROOT"
DISPOSITION_MODE_ENV = "LINEBOSS_BS_ROBOT_NATIVE_DISPOSITION_MODE"
DISPOSITION_MODE_TOKEN = (
    "ARCHIVE_TWO_FAILED_RUNS_MOVE_INVALID_NAMESPACE_AND_CLEAN_IMPORT_"
    "HIGH_ELBOW_MONOTONIC_V001_ONCE"
)


def fail(message: str) -> None:
    raise RuntimeError("BODYSHOP_ROBOT_NATIVE_PRE_CLEAN_DISPOSITION_V001_FAIL: " + message)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def is_inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def project_relative(path: Path) -> str:
    return path.resolve().relative_to(PROJECT).as_posix()


def resolve_run_root() -> Path:
    raw = os.environ.get(RUN_ROOT_ENV, "").strip()
    if not raw:
        fail(f"{RUN_ROOT_ENV} is unset; use the guarded clean-import runner")
    run_root = Path(raw).resolve()
    if run_root == AUDIT_ROOT.resolve() or not is_inside(run_root, AUDIT_ROOT):
        fail("run root escapes the dedicated audit root: " + str(run_root))
    if not run_root.is_dir():
        fail("runner-created clean-import directory is missing: " + str(run_root))
    if run_root in [PROJECT / item["root"] for item in json.loads(
            CONTRACT.read_text(encoding="utf-8-sig"))["failed_runs"]]:
        fail("current run root aliases a frozen failed run")
    return run_root


def verify_file(path: Path, expected: dict, label: str) -> None:
    if not path.is_file():
        fail(label + " is missing: " + str(path))
    if path.stat().st_size != int(expected["bytes"]) or sha256(path) != expected["sha256"]:
        fail(label + " hash/size drift: " + str(path))


def exclusive_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as source_handle, destination.open("xb") as destination_handle:
        for block in iter(lambda: source_handle.read(1024 * 1024), b""):
            destination_handle.write(block)


def mark_and_verify_read_only(path: Path) -> None:
    path.chmod(stat.S_IREAD)
    attributes = int(getattr(path.stat(), "st_file_attributes", 0))
    if not attributes & int(stat.FILE_ATTRIBUTE_READONLY):
        fail("archive file did not retain the Windows read-only attribute: " + str(path))


def copy_verified(source: Path, destination: Path, expected: dict, label: str) -> dict:
    verify_file(source, expected, label + " source")
    if destination.exists():
        fail("exclusive archive destination already exists: " + str(destination))
    exclusive_copy(source, destination)
    verify_file(destination, expected, label + " archive")
    verify_file(source, expected, label + " source after copy")
    mark_and_verify_read_only(destination)
    return {
        "source_path": str(source),
        "archived_path": project_relative(destination),
        "bytes": int(expected["bytes"]),
        "sha256": expected["sha256"],
        "archive_read_only": True,
    }


def relative_invalid_path(expected: dict, contract: dict) -> Path:
    disk_root = Path(contract["invalid_namespace"]["disk_path"])
    path = Path(expected["path"])
    try:
        return path.relative_to(disk_root)
    except ValueError:
        fail("invalid package path escapes the exact namespace: " + expected["path"])


def verify_exact_recursive_file_inventory(
        root: Path, expected_relatives: set[str], label: str) -> None:
    if not root.is_dir():
        fail(label + " root is missing: " + str(root))
    actual = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
    if actual != expected_relatives:
        fail(
            label + " recursive path inventory drift: missing="
            + repr(sorted(expected_relatives - actual))
            + " added=" + repr(sorted(actual - expected_relatives))
        )


def main() -> None:
    if Path.cwd().resolve() != PROJECT:
        fail("run from the exact project root: " + str(PROJECT))
    if not CONTRACT.is_file() or sha256(CONTRACT) != EXPECTED_CONTRACT_SHA256:
        fail("exact clean disposition contract is missing or changed")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8-sig"))
    if contract.get("status") != (
            "FROZEN__TWO_FAILED_RUNS_AND_EXACT_INVALID_NAMESPACE__"
            "ARCHIVE_AND_ATOMIC_MOVE__CLEAN_IMPORT_ONLY"):
        fail("clean disposition contract status drift")
    if (os.environ.get(DISPOSITION_MODE_ENV, "").strip() != DISPOSITION_MODE_TOKEN
            or contract.get("disposition_mode_token") != DISPOSITION_MODE_TOKEN):
        fail("exact destructive disposition acknowledgement is absent or changed")
    run_root = resolve_run_root()
    archive_contract = contract["archive_and_move"]
    receipt = run_root / archive_contract["receipt_name"]
    failure = run_root / archive_contract["failure_name"]
    failed_folder = run_root / archive_contract["failed_runs_archive_folder"]
    invalid_copy_folder = run_root / archive_contract["invalid_namespace_copy_folder"]
    move_parent = run_root / archive_contract["invalid_namespace_move_folder"]
    moved_root = move_parent / archive_contract["move_target_leaf"]
    evidence = {
        "$schema": "lineboss/audit/bodyshop-robot-native-v001-pre-clean-import-disposition/v1",
        "generated_utc": now(),
        "process_id": os.getpid(),
        "run_root": project_relative(run_root),
        "clean_disposition_contract_sha256": EXPECTED_CONTRACT_SHA256,
        "archiver_sha256": sha256(Path(__file__).resolve()),
        "stage": "PRECHECK",
        "content_packages_deleted": 0,
        "content_files_written": 0,
        "namespace_move_attempted": False,
        "namespace_move_completed": False,
    }
    try:
        outputs = (receipt, failure, failed_folder, invalid_copy_folder, move_parent)
        if any(path.exists() for path in outputs):
            fail("clean disposition output already exists; refusing replacement")
        if not DESTINATION.is_dir():
            fail("exact invalid Content namespace is absent before disposition")
        if os.path.splitdrive(str(DESTINATION))[0].casefold() != os.path.splitdrive(str(run_root))[0].casefold():
            fail("namespace and recovery archive are not on the same volume")
        for failed_run in contract["failed_runs"]:
            verify_exact_recursive_file_inventory(
                PROJECT / failed_run["root"],
                {row["path"] for row in failed_run["files"]},
                "failed run " + failed_run["id"],
            )
        expected_invalid_relatives = {
            relative_invalid_path(row, contract).as_posix()
            for row in contract["invalid_namespace"]["packages"]
        }
        verify_exact_recursive_file_inventory(
            DESTINATION, expected_invalid_relatives, "invalid Content namespace"
        )

        evidence["stage"] = "ARCHIVE_FAILED_RUNS"
        failed_archives = []
        for failed_run in contract["failed_runs"]:
            source_root = PROJECT / failed_run["root"]
            archive_root = failed_folder / failed_run["id"]
            for expected in failed_run["files"]:
                source = source_root / expected["path"]
                destination = archive_root / expected["path"]
                failed_archives.append(copy_verified(
                    source, destination, expected, "failed run " + failed_run["id"]
                ))

        evidence["stage"] = "ARCHIVE_INVALID_NAMESPACE"
        invalid_archives = []
        for expected in contract["invalid_namespace"]["packages"]:
            source = PROJECT / expected["path"]
            destination = invalid_copy_folder / expected["path"]
            invalid_archives.append(copy_verified(
                source, destination, expected, "invalid namespace package"
            ))

        # Re-prove every source immediately before the one authorized mutation.
        for failed_run in contract["failed_runs"]:
            source_root = PROJECT / failed_run["root"]
            for expected in failed_run["files"]:
                verify_file(source_root / expected["path"], expected, "failed run pre-move")
        for expected in contract["invalid_namespace"]["packages"]:
            verify_file(PROJECT / expected["path"], expected, "invalid package pre-move")
        for failed_run in contract["failed_runs"]:
            verify_exact_recursive_file_inventory(
                PROJECT / failed_run["root"],
                {row["path"] for row in failed_run["files"]},
                "failed run immediately before move " + failed_run["id"],
            )
        verify_exact_recursive_file_inventory(
            DESTINATION, expected_invalid_relatives,
            "invalid Content namespace immediately before move",
        )

        evidence["stage"] = "ATOMIC_RECOVERABLE_NAMESPACE_MOVE"
        move_parent.mkdir(parents=True, exist_ok=False)
        if moved_root.exists():
            fail("recoverable move target already exists")
        evidence["namespace_move_attempted"] = True
        DESTINATION.rename(moved_root)
        evidence["namespace_move_completed"] = True
        if DESTINATION.exists():
            fail("Content namespace still exists after atomic directory rename")
        verify_exact_recursive_file_inventory(
            moved_root, expected_invalid_relatives, "recoverably moved invalid namespace"
        )

        moved_packages = []
        for expected in contract["invalid_namespace"]["packages"]:
            path = moved_root / relative_invalid_path(expected, contract)
            verify_file(path, expected, "recoverably moved invalid package")
            mark_and_verify_read_only(path)
            moved_packages.append({
                "original_path": expected["path"],
                "moved_path": project_relative(path),
                "bytes": int(expected["bytes"]),
                "sha256": expected["sha256"],
                "moved_copy_read_only": True,
            })

        evidence.update({
            "status": (
                "PASS__TWO_FAILED_RUNS_AND_INVALID_NAMESPACE_ARCHIVED_BYTE_FOR_BYTE__"
                "INVALID_NAMESPACE_ATOMICALLY_MOVED__CONTENT_PATH_ABSENT"
            ),
            "stage": "PASS",
            "failed_run_archives": failed_archives,
            "failed_run_archive_count": len(failed_archives),
            "invalid_namespace_archives": invalid_archives,
            "invalid_namespace_archive_count": len(invalid_archives),
            "recoverably_moved_packages": moved_packages,
            "recoverably_moved_package_count": len(moved_packages),
            "source_failed_run_roots_unchanged": True,
            "content_namespace_absent": not DESTINATION.exists(),
            "copy_policy": archive_contract["copy_policy"],
            "move_policy": archive_contract["move_policy"],
            "failures": [],
        })
        with receipt.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(evidence, indent=2) + "\n")
        print(evidence["status"])
        print("DISPOSITION_RECEIPT " + str(receipt))
    except Exception as error:
        record = dict(evidence)
        record.update({
            "status": "FAIL_CLOSED__BODYSHOP_ROBOT_NATIVE_PRE_CLEAN_IMPORT_DISPOSITION_V001",
            "error": str(error),
            "traceback": traceback.format_exc(),
            "partial_archive_preserved": True,
            "content_namespace_present": DESTINATION.exists(),
            "recoverable_move_root_present": moved_root.exists(),
            "automatic_cleanup": "NOT_PERFORMED",
        })
        if not failure.exists():
            with failure.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(record, indent=2) + "\n")
        raise


if __name__ == "__main__":
    main()
