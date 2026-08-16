"""Freeze or verify the chained Cairnwell runtime recovery v003 offline."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8").resolve()
CONTRACT = PROJECT / "Scripts/cairnwell_2040_runtime_v001_import_contract.json"
CONTRACT_SHA = PROJECT / "Scripts/cairnwell_2040_runtime_v001_import_contract.sha256"
BASELINE = PROJECT / "Scripts/cairnwell_2040_runtime_v001_import_baseline.json"
BASELINE_SHA = PROJECT / "Scripts/cairnwell_2040_runtime_v001_import_baseline.sha256"
V002_CONTRACT = PROJECT / "Scripts/cairnwell_2040_runtime_v001_recovery_v002_contract.json"
V002_CONTRACT_SHA = PROJECT / "Scripts/cairnwell_2040_runtime_v001_recovery_v002_contract.sha256"
OUTPUT = PROJECT / "Scripts/cairnwell_2040_runtime_v001_recovery_v003_contract.json"
OUTPUT_SHA = PROJECT / "Scripts/cairnwell_2040_runtime_v001_recovery_v003_contract.sha256"
DEST = PROJECT / "Content/LineBoss/Factory/OneFactory/v001/Vehicles/Cairnwell2040Runtime_v001"
AUDIT_ROOT = PROJECT / "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/UnrealImportLane_v001"
V001_RUN_ID = "20260815T094919Z-7dfb3c0a"
V001_IMPORT_FAILURE_SHA256 = "05F204CDE09BD22BED823101525C82F64E18F8EE56BC6004C9E0979AA73CFC2D"
V002_RUN_ID = "20260815T103132Z-3fc39714"
V002_RUN = AUDIT_ROOT / "Recovery_v002" / V002_RUN_ID
V002_IMPORT_FAILURE_SHA256 = "86AB67E0AD2C501EE8E49CFAF6061694DD78DFD616B81F22B53B80896E127EE1"
V002_CONTRACT_SHA256 = "0D0E0ADE47D80F487A8E94547133323EF1C7622C9260177A948049BC09AA85E2"
RECOVERY_AUDIT_ROOT = AUDIT_ROOT / "Recovery_v003"
V001_QUARANTINE = (
    PROJECT / "Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
    "Incident_20260815T094919Z-7dfb3c0a_v001"
)
V002_QUARANTINE = (
    PROJECT / "Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
    "Incident_20260815T103132Z-3fc39714_v002"
)
ACK_TOKEN = "FREEZE_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V003_ONCE"
RUN_ACK_TOKEN = "RECOVER_QUARANTINED_CAIRNWELL_2040_RUNTIME_V001_V003_ONCE"
STATUS = (
    "FROZEN__CAIRNWELL_2040_RUNTIME_V001_INCIDENT_CHAINED_RECOVERY_V003__"
    "READY_FOR_ONE_SHOT_QUARANTINE_AND_TWO_PROCESS_IMPORT"
)
CONTRACT_EXPECTED_SHA256 = "B0D276A85E8532B580098092384BD93D0E5F55E3A437922FFFC31D69B8816EB1"
BASELINE_EXPECTED_SHA256 = "493CEBCA0DAA09179D0F44BE2FE4E4D60658D8F42CD88A02268045591EE77882"
V002_FILES = {
    "import_failure_recovery_v002.json": (5460, "86AB67E0AD2C501EE8E49CFAF6061694DD78DFD616B81F22B53B80896E127EE1"),
    "lane_summary_recovery_v002.json": (2921, "D152B33365F3CCBE005E7552468FDE90628AEBB21371A93831A7187BEF2146D6"),
    "quarantine_receipt_v002.json": (3205, "61185A4AF74711FEAD0E67D4026522BF5C48CB48D73CCCC0BAB76DE4A8F0CC57"),
    "unreal_import_recovery_v002.log": (359433, "138E4F06AC6B562325BE84EA8CEA4D6DBE27CCE6140FA718C9A6C6164487BB08"),
    "unreal_import_recovery_v002.stderr.log": (0, "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"),
    "unreal_import_recovery_v002.stdout.log": (359416, "DCBE73E2CA83CD6BAD6EC18ECC29983D1D20F2E82618642D7609C740BF927B69"),
}
V002_PARTIALS = {
    "Materials/M_LB_C2040_BIWGalvanized_v001.uasset": (6002, 1786790010826675900, "3B3A5D9B6195891522A219D27C19E62DDA3C891EDC664EE1E75B13615D5A3034"),
    "Materials/M_LB_C2040_BodyPaintTintPBR_v001.uasset": (11566, 1786790010882676700, "E74FA8C2EA49B1AD34D33CBD11CEF4D4A2C627490223C06A525487B8AE36208A"),
    "Materials/M_LB_C2040_EDCoat_v001.uasset": (5960, 1786790010938669000, "765F924403E6278B8604F4700ACD9DC7F89E6FF813B5DF3758952C90E8C78274"),
    "Materials/M_LB_C2040_RollingGearPBR_v001.uasset": (7119, 1786790010993668700, "57698E6F740E4D0F2C53C4FF3196AF2A4874BD04ADBE5D7A67238D713F8C8D02"),
    "Textures/T_LB_C2040_Emerald_BaseColor_v001.uasset": (3818680, 1786790010622668900, "6F902C40D9117585711E383673990B3FA7501E53CA3B9CCF76DDD377F4FE044A"),
    "Textures/T_LB_C2040_Emerald_MRBodyMask_v001.uasset": (5818244, 1786790010667676200, "CFECE87484B903B5350D98A06D05D083E247273A227E8A7DBBCC88198F9FF2B1"),
    "Textures/T_LB_C2040_Emerald_Normal_v001.uasset": (3973188, 1786790010703676400, "39BA2B508646697BD09130525A14715218C54DFA72204F51B777136CDE7CF989"),
}
V002_LANE_CHANGED = {
    "Scripts/cairnwell_2040_runtime_v001.py",
    "Scripts/import_cairnwell_2040_runtime_v001.py",
    "Scripts/validate_cairnwell_2040_runtime_fresh_process_v001.py",
    "Scripts/run_cairnwell_2040_runtime_import_lane_v001.ps1",
    "Scripts/tests/test_cairnwell_2040_runtime_import_lane_v001.py",
}
V003_ADDITIONS = {
    "Docs/OneFactory/CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V003.md",
    "Scripts/cairnwell_2040_runtime_log_retry_v003.ps1",
    "Scripts/prepare_cairnwell_2040_runtime_v001_recovery_v003.py",
}
FBX_NAME_PATTERN = re.compile(rb"MI_LB_C2040_[A-Za-z0-9_.]+")


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
        raise RecoveryError("required file missing: " + str(path))
    stat = path.stat()
    return {"path": relative(path), "bytes": stat.st_size,
            "mtime_ns": stat.st_mtime_ns, "sha256": sha256(path)}


def canonical_hash(rows: list[dict]) -> str:
    compact = [
        {key: row[key] for key in ("path", "bytes", "mtime_ns", "sha256")}
        for row in sorted(rows, key=lambda item: item["path"].casefold())
    ]
    return hashlib.sha256(
        json.dumps(compact, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest().upper()


def object_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest().upper()


def inventory(paths: list[Path]) -> dict:
    rows = [file_row(path) for path in sorted(set(paths), key=lambda p: str(p).casefold())]
    return {"file_count": len(rows), "inventory_sha256": canonical_hash(rows), "files": rows}


def exact_sidecar(payload: Path, sidecar: Path, expected: str, label: str) -> str:
    digest = sha256(payload)
    if digest != expected:
        raise RecoveryError(f"{label} hash drift: {digest}")
    if sidecar.read_text(encoding="ascii").strip().split()[0].upper() != digest:
        raise RecoveryError(label + " sidecar drift")
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
        raise RecoveryError(label + " inventory drift")


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
        selected = {path for path in selected if not any(
            path.resolve() == item.resolve() or inside(path, item) for item in exclusions)}
        if {relative(path) for path in selected} != set(group["paths"]):
            raise RecoveryError("protected path inventory drift: " + group["name"])


def load_original() -> tuple[dict, dict, str, str]:
    contract_digest = exact_sidecar(
        CONTRACT, CONTRACT_SHA, CONTRACT_EXPECTED_SHA256, "original contract")
    baseline_digest = exact_sidecar(
        BASELINE, BASELINE_SHA, BASELINE_EXPECTED_SHA256, "original baseline")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    if (baseline.get("status") != "FROZEN__CAIRNWELL_2040_RUNTIME_V001_PROJECT_BASELINE"
            or baseline.get("contract", {}).get("sha256") != contract_digest):
        raise RecoveryError("original frozen baseline identity drift")
    verify_snapshot(baseline["source"], "approved v005 source")
    verify_protected_paths(baseline["protected"])
    verify_snapshot(baseline["protected"], "protected project")
    return contract, baseline, contract_digest, baseline_digest


def load_v002_contract() -> dict:
    exact_sidecar(V002_CONTRACT, V002_CONTRACT_SHA, V002_CONTRACT_SHA256, "v002 contract")
    payload = json.loads(V002_CONTRACT.read_text(encoding="utf-8"))
    if (payload.get("$schema") != "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v2"
            or payload.get("status") != (
                "FROZEN__CAIRNWELL_2040_RUNTIME_V001_INCIDENT_BOUND_RECOVERY_V002__"
                "READY_FOR_ONE_SHOT_QUARANTINE_AND_TWO_PROCESS_IMPORT")
            or payload.get("incident", {}).get("failed_run_id") != V001_RUN_ID
            or payload.get("incident", {}).get("import_failure", {}).get("sha256")
            != V001_IMPORT_FAILURE_SHA256):
        raise RecoveryError("frozen v002 recovery authority drift")
    for row in payload["incident"]["files"].values():
        if file_row(PROJECT / row["path"]) != row:
            raise RecoveryError("preserved v001 incident drift")
    q1_paths = [PROJECT / row["quarantine_path"] for row in payload["partial_packages"].values()]
    q1 = inventory(q1_paths)
    if q1["file_count"] != 4 or not all(inside(path, V001_QUARANTINE) for path in q1_paths):
        raise RecoveryError("v001 four-package quarantine closure drift")
    return payload


def v002_run_rows() -> dict[str, dict]:
    if not V002_RUN.is_dir():
        raise RecoveryError("exact v002 failed-run root is absent")
    actual_names = {path.name for path in V002_RUN.iterdir() if path.is_file()}
    if actual_names != set(V002_FILES):
        raise RecoveryError("v002 failed-run file closure drift: " + repr(sorted(actual_names)))
    rows = {}
    for name, (size, digest) in V002_FILES.items():
        row = file_row(V002_RUN / name)
        if row["bytes"] != size or row["sha256"] != digest:
            raise RecoveryError("v002 failed-run hash drift: " + name)
        rows[name] = row
    failure = json.loads((V002_RUN / "import_failure_recovery_v002.json").read_text())
    summary = json.loads((V002_RUN / "lane_summary_recovery_v002.json").read_text())
    quarantine = json.loads((V002_RUN / "quarantine_receipt_v002.json").read_text())
    if (failure.get("$schema")
            != "lineboss/audit/cairnwell-2040-runtime-v001/recovery-v002/unreal-import/v2"
            or failure.get("status")
            != "FAIL_CLOSED__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V002_UNREAL_IMPORT"
            or failure.get("error") != (
                "CAIRNWELL_2040_RUNTIME_V001_UNREAL_LANE_FAIL: LOD0/global semantic "
                "material-slot order drift: BIW_AutomotiveSkeleton"
                "['MI_LB_C2040_BIW_GalvanisedSteel_v005_001']")
            or summary.get("status")
            != "FAIL_CLOSED__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V002_UNREAL_IMPORT_LANE"
            or "because it is being used by another process" not in str(summary.get("error"))
            or quarantine.get("status")
            != "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V002_PARTIALS_QUARANTINED"):
        raise RecoveryError("v002 primary/wrapper/quarantine incident identity drift")
    return rows


def partial_rows(root: Path, label: str) -> dict[str, dict]:
    if not root.is_dir():
        raise RecoveryError(label + " root absent")
    actual = {path.relative_to(root).as_posix(): path for path in root.rglob("*") if path.is_file()}
    if set(actual) != set(V002_PARTIALS):
        raise RecoveryError(label + " seven-package closure drift")
    rows = {}
    for rel, (size, mtime, digest) in V002_PARTIALS.items():
        row = file_row(actual[rel])
        if (row["bytes"] != size or row["mtime_ns"] != mtime or row["sha256"] != digest):
            raise RecoveryError(label + " package hash/mtime drift: " + rel)
        rows[rel] = row
    return rows


def partial_contract_rows() -> dict[str, dict]:
    current = partial_rows(DEST, "v002 fresh destination")
    failure = json.loads((V002_RUN / "import_failure_recovery_v002.json").read_text())
    preserved = failure["namespace_files_preserved_for_recovery"]
    output = {}
    for rel, row in current.items():
        source_path = relative(DEST / rel)
        if preserved.get(source_path) != {
                key: row[key] for key in ("bytes", "mtime_ns", "sha256")}:
            raise RecoveryError("v002 failure receipt does not pin package: " + source_path)
        output[source_path] = {
            "source_path": source_path,
            "quarantine_path": relative(V002_QUARANTINE / rel),
            "bytes": row["bytes"], "mtime_ns": row["mtime_ns"], "sha256": row["sha256"],
        }
    return output


def slot_normalization(contract: dict) -> dict:
    output = {}
    for role, spec in sorted(contract["modules"].items()):
        canonical = spec["material_slots"]
        if len(canonical) != 1 or len(spec["lods"]) != 3:
            raise RecoveryError("slot normalization requires one slot/three LODs: " + role)
        names = []
        counts = []
        for lod in spec["lods"]:
            source = PROJECT / lod["source"]["path"]
            matches = [value.decode("ascii") for value in FBX_NAME_PATTERN.findall(source.read_bytes())]
            unique = sorted(set(matches))
            if len(matches) != 1 or len(unique) != 1:
                raise RecoveryError(f"{role}:LOD{lod['lod']} FBX material-name count drift: {matches}")
            names.append(unique[0])
            counts.append(1)
        if len(set(names)) != 1:
            raise RecoveryError(role + " raw FBX material name differs across LODs")
        raw = names[0]
        ue_name = raw
        for character in (".", ",", "/", "`", "%"):
            ue_name = ue_name.replace(character, "_")
        normalize = raw != canonical[0]
        if role == "BIW_AutomotiveSkeleton":
            if (raw != "MI_LB_C2040_BIW_GalvanisedSteel_v005.001"
                    or ue_name != "MI_LB_C2040_BIW_GalvanisedSteel_v005_001"
                    or canonical[0] != "MI_LB_C2040_BIW_GalvanisedSteel_v005"):
                raise RecoveryError("exact BIW dotted/sanitized/canonical slot proof drift")
        elif raw != canonical[0] or ue_name != canonical[0] or normalize:
            raise RecoveryError("unexpected material-slot rewrite would be required: " + role)
        output[role] = {
            "source_fbx_material_name": raw,
            "ue_imported_material_slot_name": ue_name,
            "canonical_material_slot_name": canonical[0],
            "normalize_gameplay_material_slot_name": normalize,
            "required_static_material_count": 1,
            "source_occurrence_count_by_lod": counts,
            "engine_make_name_rule": "replace exact characters . , / ` % with underscore",
        }
    return output


def verify_v002_lane_drift(v002: dict) -> None:
    changed = set()
    for expected in v002["lane"]["files"]:
        if file_row(PROJECT / expected["path"]) != expected:
            changed.add(expected["path"])
    if changed != V002_LANE_CHANGED:
        raise RecoveryError("v002 prepared-lane drift is not exact v003 patch: " + repr(changed))


def v003_lane_snapshot(v002: dict) -> dict:
    paths = {row["path"] for row in v002["lane"]["files"]} | V003_ADDITIONS
    snapshot = inventory([PROJECT / rel for rel in paths])
    if {row["path"] for row in snapshot["files"]} != paths:
        raise RecoveryError("v003 prepared-lane path closure drift")
    return snapshot


def result_topology() -> dict:
    return {
        "audit_root": relative(RECOVERY_AUDIT_ROOT),
        "run_root_pattern": relative(RECOVERY_AUDIT_ROOT) + "/<UTC>-<GUID8>",
        "quarantine_receipt": {"filename": "quarantine_receipt_v003.json",
            "$schema": "lineboss/audit/cairnwell-2040-runtime-v001/recovery-v003/quarantine/v3",
            "pass_status": "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V003_PARTIALS_QUARANTINED"},
        "import": {"receipt_filename": "import_receipt_recovery_v003.json",
            "failure_filename": "import_failure_recovery_v003.json",
            "$schema": "lineboss/audit/cairnwell-2040-runtime-v001/recovery-v003/unreal-import/v3",
            "pass_status": "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V003_FRESH_IMPORT__4_MESHES__12_AUTHORED_LODS__3_TEXTURES__4_MATERIALS__EXACT_11_PACKAGE_CLOSURE",
            "package_hash_field": "package_sha256"},
        "fresh_validation": {"receipt_filename": "fresh_process_validation_receipt_recovery_v003.json",
            "failure_filename": "fresh_process_validation_failure_recovery_v003.json",
            "$schema": "lineboss/audit/cairnwell-2040-runtime-v001/recovery-v003/fresh-process-validation/v3",
            "pass_status": "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V003_DISTINCT_FRESH_PROCESS__READ_ONLY_RELOAD__11_PACKAGE_HASHES_UNCHANGED",
            "package_hash_fields": ["package_sha256_before_loads", "package_sha256_after_loads"]},
        "summary": {"filename": "lane_summary_recovery_v003.json",
            "$schema": "lineboss/audit/cairnwell-2040-runtime-v001/recovery-v003/import-lane-summary/v3",
            "pass_status": "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V003_GUARDED_IMPORT_AND_DISTINCT_READ_ONLY_RELOAD",
            "package_hash_field": "post_exit_package_sha256"},
        "required_incident_binding_fields": ["recovery_contract_sha256",
            "v001_failed_run_id", "v001_import_failure_sha256", "v002_failed_run_id",
            "v002_import_failure_sha256", "incident_chain_sha256", "quarantine_receipt"],
    }


def create_contract(acknowledgement: str) -> None:
    if acknowledgement != ACK_TOKEN:
        raise RecoveryError("exact v003 recovery-freeze acknowledgement missing")
    if OUTPUT.exists() or OUTPUT_SHA.exists():
        raise RecoveryError("refusing to overwrite v003 recovery contract or sidecar")
    if RECOVERY_AUDIT_ROOT.exists() or V002_QUARANTINE.exists():
        raise RecoveryError("v003 result/quarantine already exists")
    contract, baseline, contract_digest, baseline_digest = load_original()
    v002 = load_v002_contract()
    verify_v002_lane_drift(v002)
    run_rows = v002_run_rows()
    partials = partial_contract_rows()
    v001 = {
        "failed_run_id": V001_RUN_ID,
        "import_failure": v002["incident"]["import_failure"],
        "files": v002["incident"]["files"],
    }
    v002_incident = {
        "failed_run_id": V002_RUN_ID,
        "run_root": relative(V002_RUN),
        "recovery_contract": file_row(V002_CONTRACT),
        "recovery_contract_sidecar": file_row(V002_CONTRACT_SHA),
        "import_failure": run_rows["import_failure_recovery_v002.json"],
        "lane_summary": run_rows["lane_summary_recovery_v002.json"],
        "quarantine_receipt": run_rows["quarantine_receipt_v002.json"],
        "files": run_rows,
        "primary_failure": "exact source material name .001 sanitized by UE to _001",
        "wrapper_failure": "redirected stdout remained temporarily locked after process exit",
    }
    chain = {"v001": v001, "v002": v002_incident,
             "old_success_receipts_present": False}
    chain["binding_sha256"] = object_hash(chain)
    q1_paths = [PROJECT / row["quarantine_path"] for row in v002["partial_packages"].values()]
    payload = {
        "$schema": "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v3",
        "status": STATUS,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "acknowledgement": RUN_ACK_TOKEN,
        "project_root": str(PROJECT),
        "original_authorities": {"contract": file_row(CONTRACT),
            "contract_sidecar": file_row(CONTRACT_SHA), "baseline": file_row(BASELINE),
            "baseline_sidecar": file_row(BASELINE_SHA)},
        "approved_source": {key: baseline["source"][key]
                            for key in ("file_count", "inventory_sha256")},
        "protected_project": {key: baseline["protected"][key]
                              for key in ("file_count", "inventory_sha256")},
        "incident_chain": chain,
        "prior_quarantines": {"v001_partial_packages": inventory(q1_paths)},
        "partial_packages": partials,
        "slot_normalization": slot_normalization(contract),
        "ue58_source_evidence": {"path": (
            "C:/Program Files/Epic Games/UE_5.8/Engine/Source/Editor/UnrealEd/Private/"
            "Fbx/FbxMainImport.cpp"), "sha256": (
            "506DE36CC110B754D70800E964A6BCF8D38D304B94C8D8AE3E947B0351B99EF8"),
            "lines": "1870-1888", "proof": "MakeName replaces period with underscore"},
        "quarantine": {"source_root": relative(DEST),
            "destination_root": relative(V002_QUARANTINE),
            "operation": "MOVE_DIRECTORY_ONLY__NO_DELETE",
            "automatic_delete_authorized": False,
            "rerun_after_any_recovery_result_authorized": False},
        "lane": v003_lane_snapshot(v002),
        "result_topology": result_topology(),
        "policy": {"unreal_launch_authorized_by_freeze": False,
            "source_config_maps_saves_writes_authorized": False,
            "map_load_save_authorized": False,
            "runtime_binding_or_promotion_authorized": False,
            "panel_module_namespace_or_packages_authorized": False,
            "strict_editor_exit_code_zero_required": True,
            "post_receipt_fatal_or_crash_accepted": False,
            "redirected_log_hash_requires_successful_bounded_read_open": True},
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    digest = sha256(OUTPUT)
    OUTPUT_SHA.write_text(f"{digest}  {OUTPUT.name}\n", encoding="ascii")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V003_CONTRACT_FROZEN")
    print(digest)


def load_frozen() -> tuple[dict, dict]:
    contract, baseline, contract_digest, baseline_digest = load_original()
    v002 = load_v002_contract()
    verify_v002_lane_drift(v002)
    v002_run_rows()
    digest = sha256(OUTPUT)
    if OUTPUT_SHA.read_text(encoding="ascii").strip().split()[0].upper() != digest:
        raise RecoveryError("v003 recovery sidecar drift")
    payload = json.loads(OUTPUT.read_text())
    chain = payload.get("incident_chain", {})
    if (payload.get("$schema") != "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v3"
            or payload.get("status") != STATUS or payload.get("acknowledgement") != RUN_ACK_TOKEN
            or payload.get("original_authorities", {}).get("contract", {}).get("sha256")
            != contract_digest
            or payload.get("original_authorities", {}).get("baseline", {}).get("sha256")
            != baseline_digest
            or chain.get("v001", {}).get("import_failure", {}).get("sha256")
            != V001_IMPORT_FAILURE_SHA256
            or chain.get("v002", {}).get("import_failure", {}).get("sha256")
            != V002_IMPORT_FAILURE_SHA256):
        raise RecoveryError("v003 recovery contract identity drift")
    verify_snapshot(payload["prior_quarantines"]["v001_partial_packages"], "v001 quarantine")
    verify_snapshot(payload["lane"], "v003 prepared lane")
    if payload["slot_normalization"] != slot_normalization(contract):
        raise RecoveryError("v003 exact FBX material-slot proof drift")
    return payload, baseline


def verify_partial_contract(payload: dict, root: Path, label: str) -> None:
    rows = partial_rows(root, label)
    for rel, actual in rows.items():
        source = relative(DEST / rel)
        expected = payload["partial_packages"][source]
        expected_path = source if root == DEST else expected["quarantine_path"]
        if (actual["path"] != expected_path or any(
                actual[key] != expected[key] for key in ("bytes", "mtime_ns", "sha256"))):
            raise RecoveryError(label + " does not match contract: " + rel)


def verify_pre_quarantine() -> None:
    payload, _ = load_frozen()
    if V002_QUARANTINE.exists() or RECOVERY_AUDIT_ROOT.exists():
        raise RecoveryError("v003 quarantine/result already exists")
    verify_partial_contract(payload, DEST, "v002 fresh destination")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V003_PRE_QUARANTINE_REVERIFIED")
    print(sha256(OUTPUT))


def verify_post_quarantine() -> None:
    payload, _ = load_frozen()
    if DEST.exists():
        raise RecoveryError("fresh destination remains after v003 quarantine move")
    verify_partial_contract(payload, V002_QUARANTINE, "v002 package quarantine")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V003_POST_QUARANTINE_REVERIFIED")
    print(sha256(OUTPUT))


def verify_post_import() -> None:
    payload, baseline = load_frozen()
    verify_partial_contract(payload, V002_QUARANTINE, "v002 package quarantine")
    expected = set(baseline["destination"]["expected_package_paths"])
    actual = {"/Game/" + path.relative_to(PROJECT / "Content").with_suffix("").as_posix()
              for path in DEST.rglob("*.uasset")} if DEST.is_dir() else set()
    if actual != expected or len(actual) != 11:
        raise RecoveryError("post-import destination is not exact eleven-package closure")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V003_POST_IMPORT_REVERIFIED")
    print(sha256(OUTPUT))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--acknowledgement", default="")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--verify-pre-quarantine", action="store_true")
    group.add_argument("--verify-post-quarantine", action="store_true")
    group.add_argument("--verify-post-import", action="store_true")
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
