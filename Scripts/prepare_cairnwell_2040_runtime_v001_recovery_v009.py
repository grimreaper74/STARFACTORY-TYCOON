"""Dry-build, freeze, or verify incident-chained Cairnwell recovery v009 offline."""

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
import prepare_cairnwell_2040_runtime_v001_recovery_v008 as prior


BASE = prior.BASE
PROJECT = prior.PROJECT
CONTRACT = prior.CONTRACT
CONTRACT_SHA = prior.CONTRACT_SHA
BASELINE = prior.BASELINE
BASELINE_SHA = prior.BASELINE_SHA
V008_CONTRACT = prior.OUTPUT
V008_CONTRACT_SHA = prior.OUTPUT_SHA
OUTPUT = PROJECT / "Scripts/cairnwell_2040_runtime_v001_recovery_v009_contract.json"
OUTPUT_SHA = PROJECT / "Scripts/cairnwell_2040_runtime_v001_recovery_v009_contract.sha256"
DEST = prior.DEST
AUDIT_ROOT = prior.AUDIT_ROOT
RECOVERY_AUDIT_ROOT = AUDIT_ROOT / "Recovery_v009"
V007_RECOVERY_AUDIT_ROOT = prior.V007_RECOVERY_AUDIT_ROOT
V008_RECOVERY_AUDIT_ROOT = prior.RECOVERY_AUDIT_ROOT
V006_QUARANTINE = prior.V006_QUARANTINE
ACK_TOKEN = "FREEZE_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_ONCE"
RUN_ACK_TOKEN = "RECOVER_QUARANTINED_CAIRNWELL_2040_RUNTIME_V001_V009_ONCE"
STATUS = (
    "FROZEN__CAIRNWELL_2040_RUNTIME_V001_INCIDENT_CHAINED_RECOVERY_V009__"
    "READY_FOR_ONE_SHOT_QUARANTINE_AND_TWO_PROCESS_IMPORT"
)
V008_CONTRACT_BYTES = 133651
V008_CONTRACT_SHA256 = (
    "6E8E2D0E6D40A16CFF1AF5BEF31A00498C51DEADADF6CE0901D537285E5E49BD"
)
V008_SIDECAR_BYTES = 123
V008_SIDECAR_SHA256 = (
    "D082F35B000CEC489991F8F481AACA78580CCB1326356F468612C4C99CBA054F"
)
EXPECTED_IMPORT_FAILURES = {
    "v001": "05F204CDE09BD22BED823101525C82F64E18F8EE56BC6004C9E0979AA73CFC2D",
    "v002": "86AB67E0AD2C501EE8E49CFAF6061694DD78DFD616B81F22B53B80896E127EE1",
    "v003": "3FB3E1A8F27F1E4EF477C6F1E3E3AF41E53F2C8618CAC9A4E0A047F91BD60E7C",
    "v004": "D5BFCA5C8C2380587ECADDE9C64455FFD60A282D54A6FF8E27CD2E7144B494DF",
    "v005": "435D82778C83CDACAA2E59F91E04273181BA710F5D0BAFFA719A15E04A9F48BB",
    "v006": "A484FAAB8F612A0EE9FA915436B3389016D7137CB954580C499BDBBFE2A15F06",
}
V009_LANE_CHANGED = {
    "Scripts/cairnwell_2040_runtime_v001.py",
    "Scripts/import_cairnwell_2040_runtime_v001.py",
    "Scripts/validate_cairnwell_2040_runtime_fresh_process_v001.py",
    "Scripts/run_cairnwell_2040_runtime_import_lane_v001.ps1",
    "Scripts/tests/test_cairnwell_2040_runtime_import_lane_v001.py",
    "Scripts/prepare_cairnwell_2040_runtime_v001_recovery_v008.py",
}
V009_ADDITIONS = {
    "Docs/OneFactory/CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009.md",
    "Scripts/prepare_cairnwell_2040_runtime_v001_recovery_v009.py",
    "Scripts/cairnwell_2040_runtime_v001_recovery_v008_contract.json",
    "Scripts/cairnwell_2040_runtime_v001_recovery_v008_contract.sha256",
}


class RecoveryError(RuntimeError):
    pass


def exact_v008_contract(v007: dict, closures: dict) -> dict:
    if (not V008_CONTRACT.is_file()
            or V008_CONTRACT.stat().st_size != V008_CONTRACT_BYTES
            or BASE.sha256(V008_CONTRACT) != V008_CONTRACT_SHA256):
        raise RecoveryError("stale preliminary v008 contract byte/hash drift")
    if (not V008_CONTRACT_SHA.is_file()
            or V008_CONTRACT_SHA.stat().st_size != V008_SIDECAR_BYTES
            or BASE.sha256(V008_CONTRACT_SHA) != V008_SIDECAR_SHA256
            or V008_CONTRACT_SHA.read_text(encoding="ascii")
            != f"{V008_CONTRACT_SHA256}  {V008_CONTRACT.name}\n"):
        raise RecoveryError("stale preliminary v008 sidecar byte/hash/text drift")
    payload = json.loads(V008_CONTRACT.read_text(encoding="utf-8"))
    chain = copy.deepcopy(payload.get("incident_chain", {}))
    declared = chain.pop("binding_sha256", None)
    if (payload.get("$schema")
            != "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v8"
            or payload.get("status") != prior.STATUS
            or payload.get("acknowledgement") != prior.RUN_ACK_TOKEN
            or declared != prior.prior.object_hash(chain)
            or payload.get("incident_chain") != v007["incident_chain"]
            or payload.get("stale_preliminary_v007")
            != prior.stale_preliminary_authority()
            or payload.get("exact_prior_all_file_closures") != closures
            or int(payload.get("lane", {}).get("file_count", -1)) != 37
            or payload.get("policy", {}).get(
                "exact_prior_all_file_closures_required") is not True
            or payload.get("policy", {}).get(
                "stale_v007_pair_must_remain_byte_exact") is not True):
        raise RecoveryError("stale preliminary v008 contract identity drift")
    return payload


def stale_v008_authority() -> dict:
    return {
        "status": (
            "STALE__UNEXECUTED_V008_PRELIMINARY__SUPERSEDED_BY_V009_"
            "FULL_NO_WRITE_PAYLOAD_PREFLIGHT"),
        "contract": BASE.file_row(V008_CONTRACT),
        "sidecar": BASE.file_row(V008_CONTRACT_SHA),
        "reason": (
            "POST_FREEZE_PRE_QUARANTINE_CONSTANT_LOOKUP_FAILED_BEFORE_ANY_MOVE_OR_UE"),
        "recovery_v008_result_root": BASE.relative(V008_RECOVERY_AUDIT_ROOT),
        "v006_quarantine_root": BASE.relative(V006_QUARANTINE),
        "recovery_v008_result_root_absent_at_freeze": True,
        "v006_quarantine_absent_at_freeze": True,
        "unreal_or_ubt_launched_by_v008_freeze": False,
        "content_move_performed_by_v008_freeze": False,
    }


def verify_v008_lane_drift(v008: dict) -> None:
    changed = {
        row["path"] for row in v008["lane"]["files"]
        if BASE.file_row(PROJECT / row["path"]) != row
    }
    if changed != V009_LANE_CHANGED:
        raise RecoveryError(
            "v008 prepared-lane drift is not exact v009 patch: " + repr(sorted(changed)))


def v009_lane_snapshot(v008: dict) -> dict:
    paths = {row["path"] for row in v008["lane"]["files"]} | V009_ADDITIONS
    snapshot = BASE.inventory([PROJECT / path for path in paths])
    if (snapshot["file_count"] != 41
            or {row["path"] for row in snapshot["files"]} != paths):
        raise RecoveryError("v009 prepared-lane path closure drift")
    return snapshot


def result_topology() -> dict:
    prefix = "lineboss/audit/cairnwell-2040-runtime-v001/recovery-v009/"
    return {
        "audit_root": BASE.relative(RECOVERY_AUDIT_ROOT),
        "run_root_pattern": BASE.relative(RECOVERY_AUDIT_ROOT) + "/<UTC>-<GUID8>",
        "quarantine_receipt": {
            "filename": "quarantine_receipt_v009.json", "$schema": prefix + "quarantine/v9",
            "pass_status": "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_PARTIALS_QUARANTINED"},
        "import": {
            "receipt_filename": "import_receipt_recovery_v009.json",
            "failure_filename": "import_failure_recovery_v009.json",
            "$schema": prefix + "unreal-import/v9",
            "pass_status": "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_FRESH_IMPORT__4_MESHES__12_AUTHORED_LODS__3_TEXTURES__4_MATERIALS__EXACT_11_PACKAGE_CLOSURE",
            "package_hash_field": "package_sha256"},
        "fresh_validation": {
            "receipt_filename": "fresh_process_validation_receipt_recovery_v009.json",
            "failure_filename": "fresh_process_validation_failure_recovery_v009.json",
            "$schema": prefix + "fresh-process-validation/v9",
            "pass_status": "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_DISTINCT_FRESH_PROCESS__READ_ONLY_RELOAD__11_PACKAGE_HASHES_UNCHANGED",
            "package_hash_fields": ["package_sha256_before_loads", "package_sha256_after_loads"]},
        "summary": {
            "filename": "lane_summary_recovery_v009.json",
            "$schema": prefix + "import-lane-summary/v9",
            "pass_status": "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_GUARDED_IMPORT_AND_DISTINCT_READ_ONLY_RELOAD",
            "package_hash_field": "post_exit_package_sha256"},
        "required_incident_binding_fields": [
            "recovery_contract_sha256", "v001_failed_run_id", "v001_import_failure_sha256",
            "v002_failed_run_id", "v002_import_failure_sha256", "v003_failed_run_id",
            "v003_import_failure_sha256", "v004_failed_run_id", "v004_import_failure_sha256",
            "v005_failed_run_id", "v005_import_failure_sha256", "v006_failed_run_id",
            "v006_import_failure_sha256", "incident_chain_sha256", "quarantine_receipt"],
    }


def authority_state(require_unmoved_v006_destination: bool = False) -> dict:
    contract, baseline, contract_digest, baseline_digest = BASE.load_original()
    v007 = prior.exact_v007_contract()
    closures = prior.exact_prior_all_file_closures(v007)
    v008 = exact_v008_contract(v007, closures)
    verify_v008_lane_drift(v008)
    prior.verify_all_inherited_engine_sources(v007)
    prior.prior.v006_run_rows()
    if V007_RECOVERY_AUDIT_ROOT.exists() or V008_RECOVERY_AUDIT_ROOT.exists():
        raise RecoveryError("stale v007/v008 result root unexpectedly exists")
    if require_unmoved_v006_destination:
        prior.prior.partial_rows(DEST, "v006 fresh destination")
        if V006_QUARANTINE.exists():
            raise RecoveryError("reserved v006 quarantine already exists")
        if RECOVERY_AUDIT_ROOT.exists():
            raise RecoveryError("v009 result root already exists")
    return {
        "contract": contract,
        "baseline": baseline,
        "contract_digest": contract_digest,
        "baseline_digest": baseline_digest,
        "v007": v007,
        "v008": v008,
        "closures": closures,
    }


def expected_policy(v008: dict) -> dict:
    return {
        **copy.deepcopy(v008["policy"]),
        "exact_prior_all_file_closures_required": True,
        "stale_v007_pair_must_remain_byte_exact": True,
        "stale_v008_pair_must_remain_byte_exact": True,
        "no_write_full_candidate_payload_preflight_required": True,
    }


def expected_quarantine() -> dict:
    return {
        "source_root": BASE.relative(DEST),
        "destination_root": BASE.relative(V006_QUARANTINE),
        "operation": "MOVE_DIRECTORY_ONLY__NO_DELETE",
        "automatic_delete_authorized": False,
        "rerun_after_any_recovery_result_authorized": False,
    }


def candidate_generated_utc(state: dict) -> str:
    """Derive a stable candidate timestamp from the newest exact lane input row."""
    lane = v009_lane_snapshot(state["v008"])
    latest_mtime_ns = max(int(row["mtime_ns"]) for row in lane["files"])
    return datetime.fromtimestamp(
        latest_mtime_ns / 1_000_000_000, tz=timezone.utc).isoformat()


def build_candidate_payload(state: dict, generated_utc: str) -> dict:
    baseline = state["baseline"]
    v007 = state["v007"]
    v008 = state["v008"]
    return {
        "$schema": "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v9",
        "status": STATUS,
        "generated_utc": generated_utc,
        "acknowledgement": RUN_ACK_TOKEN,
        "project_root": str(PROJECT),
        "original_authorities": copy.deepcopy(v008["original_authorities"]),
        "approved_source": {key: baseline["source"][key]
                            for key in ("file_count", "inventory_sha256")},
        "protected_project": {key: baseline["protected"][key]
                              for key in ("file_count", "inventory_sha256")},
        "incident_chain": copy.deepcopy(v008["incident_chain"]),
        "stale_preliminary_v007": copy.deepcopy(v008["stale_preliminary_v007"]),
        "stale_preliminary_v008": stale_v008_authority(),
        "exact_prior_all_file_closures": copy.deepcopy(state["closures"]),
        "prior_quarantines": copy.deepcopy(v008["prior_quarantines"]),
        "partial_packages": copy.deepcopy(v008["partial_packages"]),
        "slot_normalization": copy.deepcopy(v008["slot_normalization"]),
        "runtime_uv_sanitization": copy.deepcopy(v008["runtime_uv_sanitization"]),
        "runtime_bounds_coordinate_conversion": copy.deepcopy(
            v008["runtime_bounds_coordinate_conversion"]),
        "exact_ue_enum_validation": copy.deepcopy(v008["exact_ue_enum_validation"]),
        "material_input_name_canonicalization": copy.deepcopy(
            v008["material_input_name_canonicalization"]),
        "quarantine": expected_quarantine(),
        "lane": v009_lane_snapshot(v008),
        "result_topology": result_topology(),
        "policy": expected_policy(v008),
    }


def validate_candidate_payload(payload: dict, state: dict) -> None:
    generated = payload.get("generated_utc")
    if not isinstance(generated, str):
        raise RecoveryError("v009 generated timestamp type drift")
    try:
        datetime.fromisoformat(generated)
    except ValueError as exc:
        raise RecoveryError("v009 generated timestamp is not ISO-8601") from exc
    if generated != candidate_generated_utc(state):
        raise RecoveryError("v009 generated timestamp is not the exact lane-state timestamp")
    expected = build_candidate_payload(state, generated)
    if payload != expected:
        raise RecoveryError("v009 full candidate payload differs from reconstructed authority")
    chain = copy.deepcopy(payload["incident_chain"])
    declared = chain.pop("binding_sha256", None)
    if declared != prior.prior.object_hash(chain):
        raise RecoveryError("v009 incident-chain binding hash drift")
    for version, expected_hash in EXPECTED_IMPORT_FAILURES.items():
        if payload["incident_chain"].get(version, {}).get(
                "import_failure", {}).get("sha256") != expected_hash:
            raise RecoveryError("v009 incident failure constant mismatch: " + version)
    closures = payload["exact_prior_all_file_closures"]
    if ({key: row["file_count"] for key, row in closures["incident_roots"].items()}
            != prior.INCIDENT_FILE_COUNTS
            or {key: row["root"] for key, row in closures["incident_roots"].items()}
            != prior.INCIDENT_ROOTS
            or {key: row["file_count"] for key, row in closures["quarantine_roots"].items()}
            != prior.QUARANTINE_FILE_COUNTS
            or {key: row["root"] for key, row in closures["quarantine_roots"].items()}
            != prior.QUARANTINE_ROOTS):
        raise RecoveryError("v009 exact prior root/count closure authority drift")
    if (payload["stale_preliminary_v007"]["contract"]["sha256"]
            != prior.V007_CONTRACT_SHA256
            or payload["stale_preliminary_v007"]["sidecar"]["sha256"]
            != prior.V007_SIDECAR_SHA256
            or payload["stale_preliminary_v008"]["contract"]["sha256"]
            != V008_CONTRACT_SHA256
            or payload["stale_preliminary_v008"]["sidecar"]["sha256"]
            != V008_SIDECAR_SHA256
            or len(payload["partial_packages"]) != 11
            or payload["lane"]["file_count"] != 41):
        raise RecoveryError("v009 stale-pair/package/lane closure drift")
    prior.verify_all_inherited_engine_sources(state["v007"])


def dry_build_payload(require_output_absent: bool = True) -> tuple[dict, str, int]:
    if require_output_absent and (OUTPUT.exists() or OUTPUT_SHA.exists()):
        raise RecoveryError("v009 dry-build requires absent contract and sidecar")
    state = authority_state(require_unmoved_v006_destination=True)
    payload = build_candidate_payload(state, candidate_generated_utc(state))
    validate_candidate_payload(payload, state)
    serialized = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    round_trip = json.loads(serialized.decode("utf-8"))
    validate_candidate_payload(round_trip, state)
    digest = __import__("hashlib").sha256(serialized).hexdigest().upper()
    return payload, digest, len(serialized)


def create_contract(acknowledgement: str) -> None:
    if acknowledgement != ACK_TOKEN:
        raise RecoveryError("exact v009 recovery-freeze acknowledgement missing")
    if OUTPUT.exists() or OUTPUT_SHA.exists():
        raise RecoveryError("refusing to overwrite v009 recovery contract or sidecar")
    state = authority_state(require_unmoved_v006_destination=True)
    payload = build_candidate_payload(state, candidate_generated_utc(state))
    validate_candidate_payload(payload, state)
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    validate_candidate_payload(json.loads(serialized), state)
    OUTPUT.write_text(serialized, encoding="utf-8", newline="\n")
    digest = BASE.sha256(OUTPUT)
    OUTPUT_SHA.write_text(
        f"{digest}  {OUTPUT.name}\n", encoding="ascii", newline="\n")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_CONTRACT_FROZEN")
    print(digest)


def load_frozen() -> tuple[dict, dict]:
    state = authority_state()
    if not OUTPUT.is_file() or not OUTPUT_SHA.is_file():
        raise RecoveryError("v009 recovery contract/sidecar absent")
    digest = BASE.sha256(OUTPUT)
    if OUTPUT_SHA.read_text(encoding="ascii") != f"{digest}  {OUTPUT.name}\n":
        raise RecoveryError("v009 recovery sidecar drift")
    payload = json.loads(OUTPUT.read_text(encoding="utf-8"))
    validate_candidate_payload(payload, state)
    BASE.verify_snapshot(payload["lane"], "v009 prepared lane")
    return payload, state["baseline"]


def verify_partial_contract(payload: dict, root: Path, label: str) -> None:
    if not root.is_dir():
        raise RecoveryError(label + " root absent")
    actual = {
        path.relative_to(root).as_posix(): path
        for path in root.rglob("*") if path.is_file()
    }
    if set(actual) != set(prior.prior.V006_PARTIAL_HASHES) or len(actual) != 11:
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
            or V007_RECOVERY_AUDIT_ROOT.exists() or V008_RECOVERY_AUDIT_ROOT.exists()):
        raise RecoveryError("v009 reserved quarantine/result topology is not absent")
    verify_partial_contract(payload, DEST, "v006 fresh destination")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_PRE_QUARANTINE_REVERIFIED")
    print(BASE.sha256(OUTPUT))


def verify_post_quarantine() -> None:
    payload, _ = load_frozen()
    if DEST.exists():
        raise RecoveryError("fresh destination remains after v009 quarantine move")
    verify_partial_contract(payload, V006_QUARANTINE, "v006 package quarantine")
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_POST_QUARANTINE_REVERIFIED")
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
    print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_POST_IMPORT_REVERIFIED")
    print(BASE.sha256(OUTPUT))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--acknowledgement", default="")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-build", action="store_true")
    group.add_argument("--verify-pre-quarantine", action="store_true")
    group.add_argument("--verify-post-quarantine", action="store_true")
    group.add_argument("--verify-post-import", action="store_true")
    args = parser.parse_args()
    if args.dry_build:
        _, digest, size = dry_build_payload()
        print("PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_NO_WRITE_FULL_PAYLOAD_PREFLIGHT")
        print(digest)
        print(size)
    elif args.verify_pre_quarantine:
        verify_pre_quarantine()
    elif args.verify_post_quarantine:
        verify_post_quarantine()
    elif args.verify_post_import:
        verify_post_import()
    else:
        create_contract(args.acknowledgement)


if __name__ == "__main__":
    main()
