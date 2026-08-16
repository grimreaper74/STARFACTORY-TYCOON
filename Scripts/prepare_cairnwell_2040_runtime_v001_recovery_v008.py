"""Freeze or verify incident-chained Cairnwell runtime recovery v008 offline."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import prepare_cairnwell_2040_runtime_v001_recovery_v007 as prior


BASE = prior.BASE
PROJECT = prior.PROJECT
CONTRACT = prior.CONTRACT
CONTRACT_SHA = prior.CONTRACT_SHA
BASELINE = prior.BASELINE
BASELINE_SHA = prior.BASELINE_SHA
V007_CONTRACT = prior.OUTPUT
V007_CONTRACT_SHA = prior.OUTPUT_SHA
OUTPUT = PROJECT / "Scripts/cairnwell_2040_runtime_v001_recovery_v008_contract.json"
OUTPUT_SHA = PROJECT / "Scripts/cairnwell_2040_runtime_v001_recovery_v008_contract.sha256"
DEST = prior.DEST
AUDIT_ROOT = prior.AUDIT_ROOT
RECOVERY_AUDIT_ROOT = AUDIT_ROOT / "Recovery_v008"
V007_RECOVERY_AUDIT_ROOT = prior.RECOVERY_AUDIT_ROOT
V006_QUARANTINE = prior.V006_QUARANTINE
ACK_TOKEN = "FREEZE_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V008_ONCE"
RUN_ACK_TOKEN = "RECOVER_QUARANTINED_CAIRNWELL_2040_RUNTIME_V001_V008_ONCE"
STATUS = (
    "FROZEN__CAIRNWELL_2040_RUNTIME_V001_INCIDENT_CHAINED_RECOVERY_V008__"
    "READY_FOR_ONE_SHOT_QUARANTINE_AND_TWO_PROCESS_IMPORT"
)
V007_CONTRACT_BYTES = 98751
V007_CONTRACT_SHA256 = (
    "7271F549ADF301C078636C408B49C5998CE8882A07FB999EF730CB0B97F7698F"
)
V007_SIDECAR_BYTES = 123
V007_SIDECAR_SHA256 = (
    "ECC793B9319E935EC29762420421292828B7ADF7C0DBBC93022C3154298F8508"
)
V008_LANE_CHANGED = {
    "Scripts/cairnwell_2040_runtime_v001.py",
    "Scripts/import_cairnwell_2040_runtime_v001.py",
    "Scripts/validate_cairnwell_2040_runtime_fresh_process_v001.py",
    "Scripts/run_cairnwell_2040_runtime_import_lane_v001.ps1",
    "Scripts/tests/test_cairnwell_2040_runtime_import_lane_v001.py",
}
V008_ADDITIONS = {
    "Docs/OneFactory/CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V008.md",
    "Scripts/prepare_cairnwell_2040_runtime_v001_recovery_v008.py",
    "Scripts/cairnwell_2040_runtime_v001_recovery_v007_contract.json",
    "Scripts/cairnwell_2040_runtime_v001_recovery_v007_contract.sha256",
}
INCIDENT_ROOTS = {
    "v001": (
        "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
        "UnrealImportLane_v001/20260815T094919Z-7dfb3c0a"),
    "v002": (
        "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
        "UnrealImportLane_v001/Recovery_v002/20260815T103132Z-3fc39714"),
    "v003": (
        "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
        "UnrealImportLane_v001/Recovery_v003/20260815T105958Z-79a98abc"),
    "v004": (
        "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
        "UnrealImportLane_v001/Recovery_v004/20260815T112446Z-4e34bb5c"),
    "v005": (
        "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
        "UnrealImportLane_v001/Recovery_v005/20260815T115847Z-92ea69dd"),
    "v006": (
        "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
        "UnrealImportLane_v001/Recovery_v006/20260815T124823Z-67c989ee"),
}
INCIDENT_FILE_COUNTS = {
    "v001": 5, "v002": 6, "v003": 6, "v004": 6, "v005": 6, "v006": 6,
}
QUARANTINE_ROOTS = {
    "v001": (
        "Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
        "Incident_20260815T094919Z-7dfb3c0a_v001"),
    "v002": (
        "Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
        "Incident_20260815T103132Z-3fc39714_v002"),
    "v003": (
        "Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
        "Incident_20260815T105958Z-79a98abc_v003"),
    "v004": (
        "Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
        "Incident_20260815T112446Z-4e34bb5c_v004"),
    "v005": (
        "Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
        "Incident_20260815T115847Z-92ea69dd_v005"),
}
QUARANTINE_FILE_COUNTS = {
    "v001": 4, "v002": 7, "v003": 11, "v004": 11, "v005": 11,
}
QUARANTINE_KEYS = {
    "v001": "v001_partial_packages",
    "v002": "v002_partial_packages",
    "v003": "v003_partial_packages",
    "v004": "v004_partial_packages",
    "v005": "v005_partial_packages",
}


class RecoveryError(RuntimeError):
    pass


def verify_all_inherited_engine_sources(payload: dict) -> None:
    authorities = {
        "material_input/" + label: row
        for label, row in payload.get(
            "material_input_name_canonicalization", {}).get(
                "engine_sources", {}).items()
    }
    authorities["enum_wrapper"] = payload.get(
        "exact_ue_enum_validation", {}).get("engine_source", {})
    authorities["fbx_uv"] = payload.get(
        "runtime_uv_sanitization", {}).get("engine_source", {})
    authorities.update({
        "bounds/" + label: row
        for label, row in payload.get(
            "runtime_bounds_coordinate_conversion", {}).get(
                "engine_sources", {}).items()
    })
    paths = [str(row.get("path", "")) for row in authorities.values()]
    if len(authorities) != 14 or len(set(paths)) != 14:
        raise RecoveryError("stale v007 inherited engine-source closure drift")
    expected_root = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine").resolve()
    for label, row in authorities.items():
        path = Path(str(row.get("path", ""))).resolve()
        if (not path.is_file() or not BASE.inside(path, expected_root)
                or len(str(row.get("sha256", ""))) != 64
                or BASE.sha256(path) != row.get("sha256")):
            raise RecoveryError("stale v007 inherited engine-source drift: " + label)


def exact_v007_contract() -> dict:
    if (not V007_CONTRACT.is_file()
            or V007_CONTRACT.stat().st_size != V007_CONTRACT_BYTES
            or BASE.sha256(V007_CONTRACT) != V007_CONTRACT_SHA256):
        raise RecoveryError("stale preliminary v007 contract byte/hash drift")
    if (not V007_CONTRACT_SHA.is_file()
            or V007_CONTRACT_SHA.stat().st_size != V007_SIDECAR_BYTES
            or BASE.sha256(V007_CONTRACT_SHA) != V007_SIDECAR_SHA256
            or V007_CONTRACT_SHA.read_text(encoding="ascii")
            != f"{V007_CONTRACT_SHA256}  {V007_CONTRACT.name}\n"):
        raise RecoveryError("stale preliminary v007 sidecar byte/hash/text drift")
    payload = json.loads(V007_CONTRACT.read_text(encoding="utf-8"))
    chain = copy.deepcopy(payload.get("incident_chain", {}))
    declared = chain.pop("binding_sha256", None)
    if (payload.get("$schema")
            != "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v7"
            or payload.get("status") != prior.STATUS
            or payload.get("acknowledgement") != prior.RUN_ACK_TOKEN
            or declared != prior.object_hash(chain)
            or set(chain) != {"v001", "v002", "v003", "v004", "v005", "v006",
                              "old_success_receipts_present"}
            or chain.get("old_success_receipts_present") is not False
            or int(payload.get("lane", {}).get("file_count", -1)) != 33):
        raise RecoveryError("stale preliminary v007 contract identity drift")
    for version in ("v002", "v003", "v004", "v005", "v006"):
        incident = payload["incident_chain"][version]
        for label in ("recovery_contract", "recovery_contract_sidecar"):
            row = incident.get(label, {})
            if BASE.file_row(PROJECT / row.get("path", "")) != row:
                raise RecoveryError(f"stale v007-pinned {version} {label} drift")
    if set(payload.get("original_authorities", {})) != {
            "contract", "contract_sidecar", "baseline", "baseline_sidecar"}:
        raise RecoveryError("stale v007 original-authority key closure drift")
    for label, row in payload["original_authorities"].items():
        if BASE.file_row(PROJECT / row.get("path", "")) != row:
            raise RecoveryError("stale v007-pinned original authority drift: " + label)
    diagnostic = payload.get("exact_ue_enum_validation", {}).get(
        "read_only_diagnostic", {})
    enum_source = payload.get("exact_ue_enum_validation", {}).get("engine_source", {})
    enum_source_path = Path(str(enum_source.get("path", "")))
    if (enum_source.get("path") != (
            "C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Experimental/"
            "PythonScriptPlugin/Source/PythonScriptPlugin/Private/PyWrapperEnum.cpp")
            or enum_source.get("sha256")
            != "54488C18B0C2916E89BF416EAC8F008E79AF430AC2F4EA8299A603D5809693AA"
            or enum_source.get("repr_lines") != "378-385"
            or enum_source.get("exact_comparison_lines") != "388-410"
            or not enum_source_path.is_file()
            or BASE.sha256(enum_source_path) != enum_source["sha256"]):
        raise RecoveryError("stale v007-pinned UE enum-wrapper source drift")
    if len(diagnostic.get("files", {})) != 8:
        raise RecoveryError("stale v007 texture-forensic file closure drift")
    for label, row in diagnostic["files"].items():
        if BASE.file_row(PROJECT / row.get("path", "")) != row:
            raise RecoveryError("stale v007-pinned texture forensic drift: " + label)
    receipt = diagnostic.get("receipt", {})
    if BASE.file_row(PROJECT / receipt.get("path", "")) != receipt:
        raise RecoveryError("stale v007-pinned texture forensic receipt drift")
    verify_all_inherited_engine_sources(payload)
    return payload


def exact_directory_snapshot(
        root_relative: str, declared_rows: list[dict], expected_count: int,
        label: str) -> dict:
    root = (PROJECT / root_relative).resolve()
    if not root.is_dir() or not BASE.inside(root, PROJECT):
        raise RecoveryError(label + " exact root absent or escapes project")
    if len(declared_rows) != expected_count:
        raise RecoveryError(label + " declared file-count authority drift")
    expected_paths = {str(row.get("path", "")) for row in declared_rows}
    actual_paths = {
        BASE.relative(path) for path in root.rglob("*") if path.is_file()
    }
    if (len(expected_paths) != expected_count or len(actual_paths) != expected_count
            or expected_paths != actual_paths):
        raise RecoveryError(
            label + " exact all-file closure drift: expected="
            + repr(sorted(expected_paths)) + " actual=" + repr(sorted(actual_paths)))
    for row in declared_rows:
        path = PROJECT / row["path"]
        if not BASE.inside(path, root) or BASE.file_row(path) != row:
            raise RecoveryError(label + " exact file-row drift: " + row["path"])
    snapshot = BASE.inventory([PROJECT / path for path in expected_paths])
    if (snapshot["file_count"] != expected_count
            or {row["path"] for row in snapshot["files"]} != expected_paths):
        raise RecoveryError(label + " exact inventory drift")
    return {"root": root_relative, **snapshot}


def exact_prior_all_file_closures(v007: dict) -> dict:
    chain = v007["incident_chain"]
    incidents = {}
    for version, root in INCIDENT_ROOTS.items():
        incident = chain[version]
        if version != "v001" and incident.get("run_root") != root:
            raise RecoveryError("preserved incident root authority drift: " + version)
        rows = list(incident.get("files", {}).values())
        incidents[version] = exact_directory_snapshot(
            root, rows, INCIDENT_FILE_COUNTS[version], "preserved incident " + version)
    quarantines = {}
    for version, root in QUARANTINE_ROOTS.items():
        snapshot = v007["prior_quarantines"][QUARANTINE_KEYS[version]]
        if int(snapshot.get("file_count", -1)) != QUARANTINE_FILE_COUNTS[version]:
            raise RecoveryError("preserved quarantine count authority drift: " + version)
        quarantines[version] = exact_directory_snapshot(
            root, list(snapshot.get("files", [])), QUARANTINE_FILE_COUNTS[version],
            "preserved quarantine " + version)
    return {"incident_roots": incidents, "quarantine_roots": quarantines}


def stale_preliminary_authority() -> dict:
    return {
        "status": "STALE__UNEXECUTED_V007_PRELIMINARY__SUPERSEDED_BY_V008_EXACT_CLOSURE",
        "contract": BASE.file_row(V007_CONTRACT),
        "sidecar": BASE.file_row(V007_CONTRACT_SHA),
        "recovery_v007_result_root": BASE.relative(V007_RECOVERY_AUDIT_ROOT),
        "v006_quarantine_root": BASE.relative(V006_QUARANTINE),
        "recovery_v007_result_root_absent_at_freeze": True,
        "v006_quarantine_absent_at_freeze": True,
        "unreal_or_ubt_launched_by_v007_freeze": False,
        "content_move_performed_by_v007_freeze": False,
    }


def verify_v007_lane_drift(v007: dict) -> None:
    changed = {
        row["path"] for row in v007["lane"]["files"]
        if BASE.file_row(PROJECT / row["path"]) != row
    }
    if changed != V008_LANE_CHANGED:
        raise RecoveryError(
            "v007 prepared-lane drift is not exact v008 patch: " + repr(sorted(changed)))


def v008_lane_snapshot(v007: dict) -> dict:
    paths = {row["path"] for row in v007["lane"]["files"]} | V008_ADDITIONS
    snapshot = BASE.inventory([PROJECT / path for path in paths])
    if (snapshot["file_count"] != 37
            or {row["path"] for row in snapshot["files"]} != paths):
        raise RecoveryError("v008 prepared-lane path closure drift")
    return snapshot


def result_topology() -> dict:
    prefix = "lineboss/audit/cairnwell-2040-runtime-v001/recovery-v008/"
    return {
        "audit_root": BASE.relative(RECOVERY_AUDIT_ROOT),
        "run_root_pattern": BASE.relative(RECOVERY_AUDIT_ROOT) + "/<UTC>-<GUID8>",
        "quarantine_receipt": {
            "filename": "quarantine_receipt_v008.json", "$schema": prefix + "quarantine/v8",
            "pass_status": "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V008_PARTIALS_QUARANTINED"},
        "import": {
            "receipt_filename": "import_receipt_recovery_v008.json",
            "failure_filename": "import_failure_recovery_v008.json",
            "$schema": prefix + "unreal-import/v8",
            "pass_status": "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V008_FRESH_IMPORT__4_MESHES__12_AUTHORED_LODS__3_TEXTURES__4_MATERIALS__EXACT_11_PACKAGE_CLOSURE",
            "package_hash_field": "package_sha256"},
        "fresh_validation": {
            "receipt_filename": "fresh_process_validation_receipt_recovery_v008.json",
            "failure_filename": "fresh_process_validation_failure_recovery_v008.json",
            "$schema": prefix + "fresh-process-validation/v8",
            "pass_status": "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V008_DISTINCT_FRESH_PROCESS__READ_ONLY_RELOAD__11_PACKAGE_HASHES_UNCHANGED",
            "package_hash_fields": ["package_sha256_before_loads", "package_sha256_after_loads"]},
        "summary": {
            "filename": "lane_summary_recovery_v008.json",
            "$schema": prefix + "import-lane-summary/v8",
            "pass_status": "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V008_GUARDED_IMPORT_AND_DISTINCT_READ_ONLY_RELOAD",
            "package_hash_field": "post_exit_package_sha256"},
        "required_incident_binding_fields": [
            "recovery_contract_sha256", "v001_failed_run_id", "v001_import_failure_sha256",
            "v002_failed_run_id", "v002_import_failure_sha256", "v003_failed_run_id",
            "v003_import_failure_sha256", "v004_failed_run_id", "v004_import_failure_sha256",
            "v005_failed_run_id", "v005_import_failure_sha256", "v006_failed_run_id",
            "v006_import_failure_sha256", "incident_chain_sha256", "quarantine_receipt"],
    }


def prior_state(require_unmoved_v006_destination: bool = False) -> tuple[
        dict, dict, dict, dict, str, str]:
    contract, baseline, contract_digest, baseline_digest = BASE.load_original()
    v007 = exact_v007_contract()
    closures = exact_prior_all_file_closures(v007)
    verify_v007_lane_drift(v007)
    prior.external_source_rows()
    prior.v006_run_rows()
    if V007_RECOVERY_AUDIT_ROOT.exists():
        raise RecoveryError("stale preliminary v007 result root unexpectedly exists")
    if require_unmoved_v006_destination:
        prior.partial_rows(DEST, "v006 fresh destination")
        if V006_QUARANTINE.exists():
            raise RecoveryError("reserved v006 quarantine already exists")
    return contract, baseline, v007, closures, contract_digest, baseline_digest


def create_contract(acknowledgement: str) -> None:
    if acknowledgement != ACK_TOKEN:
        raise RecoveryError("exact v008 recovery-freeze acknowledgement missing")
    if OUTPUT.exists() or OUTPUT_SHA.exists():
        raise RecoveryError("refusing to overwrite v008 recovery contract or sidecar")
    if RECOVERY_AUDIT_ROOT.exists():
        raise RecoveryError("v008 result root already exists")
    contract, baseline, v007, closures, _, _ = prior_state(
        require_unmoved_v006_destination=True)
    payload = {
        "$schema": "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v8",
        "status": STATUS,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "acknowledgement": RUN_ACK_TOKEN,
        "project_root": str(PROJECT),
        "original_authorities": copy.deepcopy(v007["original_authorities"]),
        "approved_source": {key: baseline["source"][key]
                            for key in ("file_count", "inventory_sha256")},
        "protected_project": {key: baseline["protected"][key]
                              for key in ("file_count", "inventory_sha256")},
        "incident_chain": copy.deepcopy(v007["incident_chain"]),
        "stale_preliminary_v007": stale_preliminary_authority(),
        "exact_prior_all_file_closures": closures,
        "prior_quarantines": copy.deepcopy(v007["prior_quarantines"]),
        "partial_packages": prior.partial_contract_rows(),
        "slot_normalization": copy.deepcopy(v007["slot_normalization"]),
        "runtime_uv_sanitization": copy.deepcopy(v007["runtime_uv_sanitization"]),
        "runtime_bounds_coordinate_conversion": copy.deepcopy(
            v007["runtime_bounds_coordinate_conversion"]),
        "exact_ue_enum_validation": copy.deepcopy(v007["exact_ue_enum_validation"]),
        "material_input_name_canonicalization": copy.deepcopy(
            v007["material_input_name_canonicalization"]),
        "quarantine": {
            "source_root": BASE.relative(DEST),
            "destination_root": BASE.relative(V006_QUARANTINE),
            "operation": "MOVE_DIRECTORY_ONLY__NO_DELETE",
            "automatic_delete_authorized": False,
            "rerun_after_any_recovery_result_authorized": False},
        "lane": v008_lane_snapshot(v007),
        "result_topology": result_topology(),
        "policy": {
            **copy.deepcopy(v007["policy"]),
            "exact_prior_all_file_closures_required": True,
            "stale_v007_pair_must_remain_byte_exact": True,
        },
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    digest = BASE.sha256(OUTPUT)
    OUTPUT_SHA.write_text(f"{digest}  {OUTPUT.name}\n", encoding="ascii")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V008_CONTRACT_FROZEN")
    print(digest)


def load_frozen() -> tuple[dict, dict]:
    _, baseline, v007, closures, contract_digest, baseline_digest = prior_state()
    if not OUTPUT.is_file() or not OUTPUT_SHA.is_file():
        raise RecoveryError("v008 recovery contract/sidecar absent")
    digest = BASE.sha256(OUTPUT)
    if OUTPUT_SHA.read_text(encoding="ascii") != f"{digest}  {OUTPUT.name}\n":
        raise RecoveryError("v008 recovery sidecar drift")
    payload = json.loads(OUTPUT.read_text(encoding="utf-8"))
    chain = copy.deepcopy(payload.get("incident_chain", {}))
    declared = chain.pop("binding_sha256", None)
    expected_failures = {
        "v001": BASE.V001_IMPORT_FAILURE_SHA256,
        "v002": BASE.V002_IMPORT_FAILURE_SHA256,
        "v003": prior.prior.prior.prior.V003_IMPORT_FAILURE_SHA256,
        "v004": prior.prior.prior.V004_IMPORT_FAILURE_SHA256,
        "v005": prior.prior.V005_IMPORT_FAILURE_SHA256,
        "v006": prior.V006_IMPORT_FAILURE_SHA256,
    }
    expected_lane = v008_lane_snapshot(v007)
    expected_quarantine = {
        "source_root": BASE.relative(DEST),
        "destination_root": BASE.relative(V006_QUARANTINE),
        "operation": "MOVE_DIRECTORY_ONLY__NO_DELETE",
        "automatic_delete_authorized": False,
        "rerun_after_any_recovery_result_authorized": False,
    }
    expected_policy = {
        **copy.deepcopy(v007["policy"]),
        "exact_prior_all_file_closures_required": True,
        "stale_v007_pair_must_remain_byte_exact": True,
    }
    if (payload.get("$schema")
            != "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v8"
            or payload.get("status") != STATUS
            or payload.get("acknowledgement") != RUN_ACK_TOKEN
            or payload.get("project_root") != str(PROJECT)
            or declared != prior.object_hash(chain)
            or payload.get("incident_chain") != v007["incident_chain"]
            or payload.get("original_authorities") != v007["original_authorities"]
            or payload.get("original_authorities", {}).get("contract", {}).get("sha256")
            != contract_digest
            or payload.get("original_authorities", {}).get("baseline", {}).get("sha256")
            != baseline_digest
            or payload.get("approved_source") != {
                key: baseline["source"][key]
                for key in ("file_count", "inventory_sha256")}
            or payload.get("protected_project") != {
                key: baseline["protected"][key]
                for key in ("file_count", "inventory_sha256")}
            or any(payload["incident_chain"].get(version, {}).get(
                "import_failure", {}).get("sha256") != expected
                   for version, expected in expected_failures.items())
            or payload.get("stale_preliminary_v007") != stale_preliminary_authority()
            or payload.get("exact_prior_all_file_closures") != closures
            or payload.get("prior_quarantines") != v007["prior_quarantines"]
            or payload.get("partial_packages") != v007["partial_packages"]
            or payload.get("quarantine") != expected_quarantine
            or payload.get("lane") != expected_lane
            or payload.get("result_topology") != result_topology()
            or payload.get("policy") != expected_policy):
        raise RecoveryError("v008 recovery identity/chronology drift")
    if V007_RECOVERY_AUDIT_ROOT.exists():
        raise RecoveryError("stale preliminary v007 result root unexpectedly exists")
    BASE.verify_snapshot(expected_lane, "v008 prepared lane")
    for inherited in (
            "slot_normalization", "runtime_uv_sanitization",
            "runtime_bounds_coordinate_conversion", "exact_ue_enum_validation",
            "material_input_name_canonicalization"):
        if payload[inherited] != v007[inherited]:
            raise RecoveryError("v008 inherited authority drift: " + inherited)
    return payload, baseline


def verify_partial_contract(payload: dict, root: Path, label: str) -> None:
    if not root.is_dir():
        raise RecoveryError(label + " root absent")
    actual = {
        path.relative_to(root).as_posix(): path
        for path in root.rglob("*") if path.is_file()
    }
    if set(actual) != set(prior.V006_PARTIAL_HASHES) or len(actual) != 11:
        raise RecoveryError(label + " exact eleven-package closure drift")
    for rel, path in actual.items():
        source = BASE.relative(DEST / rel)
        expected = payload["partial_packages"][source]
        expected_path = source if root == DEST else expected["quarantine_path"]
        row = BASE.file_row(path)
        if (row["path"] != expected_path or any(
                row[key] != expected[key] for key in ("bytes", "mtime_ns", "sha256"))):
            raise RecoveryError(label + " package row drift: " + rel)


def verify_pre_quarantine() -> None:
    payload, _ = load_frozen()
    if (V006_QUARANTINE.exists() or RECOVERY_AUDIT_ROOT.exists()
            or V007_RECOVERY_AUDIT_ROOT.exists()):
        raise RecoveryError("v008 reserved quarantine/result topology is not absent")
    verify_partial_contract(payload, DEST, "v006 fresh destination")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V008_PRE_QUARANTINE_REVERIFIED")
    print(BASE.sha256(OUTPUT))


def verify_post_quarantine() -> None:
    payload, _ = load_frozen()
    if DEST.exists():
        raise RecoveryError("fresh destination remains after v008 quarantine move")
    verify_partial_contract(payload, V006_QUARANTINE, "v006 package quarantine")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V008_POST_QUARANTINE_REVERIFIED")
    print(BASE.sha256(OUTPUT))


def verify_post_import() -> None:
    payload, baseline = load_frozen()
    verify_partial_contract(payload, V006_QUARANTINE, "v006 package quarantine")
    expected_packages = set(baseline["destination"]["expected_package_paths"])
    expected_disk = {
        spec["disk_path"]
        for collection in (baseline["modules"], baseline["textures"], baseline["materials"])
        for spec in collection.values()
    }
    actual_disk = {
        BASE.relative(path) for path in DEST.rglob("*") if path.is_file()
    } if DEST.is_dir() else set()
    actual_packages = {
        "/Game/" + (PROJECT / path).relative_to(PROJECT / "Content").with_suffix("").as_posix()
        for path in actual_disk if path.endswith(".uasset")
    }
    if (actual_disk != expected_disk or len(actual_disk) != 11
            or actual_packages != expected_packages or len(actual_packages) != 11):
        raise RecoveryError(
            "post-import destination is not exact all-file eleven-package closure: "
            + repr(sorted(actual_disk)))
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V008_POST_IMPORT_REVERIFIED")
    print(BASE.sha256(OUTPUT))


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
