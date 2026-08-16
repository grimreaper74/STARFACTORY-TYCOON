"""Validation-only fresh-process recovery for the completed v009 Cairnwell import."""

from __future__ import annotations

import copy
import json
import os
import re
import sys
import traceback
from pathlib import Path

import unreal


SCRIPTS = Path(unreal.Paths.project_dir()).resolve() / "Scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import cairnwell_2040_runtime_v001 as core
import prepare_cairnwell_2040_runtime_v001_recovery_v010 as recovery


VALIDATION_PASS = (
    "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V010_DISTINCT_FRESH_PROCESS__"
    "READ_ONLY_RELOAD_OF_V009_PASS_IMPORT__11_PACKAGE_HASHES_UNCHANGED"
)
VALIDATION_SCHEMA = (
    "lineboss/audit/cairnwell-2040-runtime-v001/recovery-v010/"
    "fresh-process-validation/v10"
)
VALIDATION_RECEIPT = "fresh_process_validation_receipt_recovery_v010.json"
VALIDATION_FAILURE = "fresh_process_validation_failure_recovery_v010.json"
RUN_ROOT_ENV = "LINEBOSS_CAIRNWELL_2040_RUNTIME_V001_RUN_ROOT"
ACK_ENV = "LINEBOSS_CAIRNWELL_2040_RUNTIME_V001_ACK"


def run_root() -> Path:
    raw = os.environ.get(RUN_ROOT_ENV, "").strip()
    if os.environ.get(ACK_ENV, "").strip() != recovery.RUN_ACK_TOKEN:
        raise RuntimeError("v010 guarded-run acknowledgement absent")
    path = Path(raw).resolve()
    if (path.parent != recovery.RECOVERY_AUDIT_ROOT.resolve()
            or not re.fullmatch(r"\d{8}T\d{6}Z-[0-9a-f]{8}", path.name)
            or not path.is_dir()):
        raise RuntimeError("v010 run root escapes or is absent: " + str(path))
    return path


def load_validation_baseline() -> tuple[dict, dict, dict]:
    recovery_payload, state = recovery.load_frozen()
    baseline = copy.deepcopy(state["baseline"])
    baseline["_contract_sha256"] = state["contract_digest"]
    baseline["_baseline_sha256"] = state["baseline_digest"]
    baseline["_recovery"] = recovery_payload
    baseline["_recovery_contract_sha256"] = core.sha256(recovery.OUTPUT)
    return baseline, recovery_payload, state


def main() -> None:
    root = run_root()
    receipt = root / VALIDATION_RECEIPT
    failure = root / VALIDATION_FAILURE
    evidence = {
        "$schema": VALIDATION_SCHEMA,
        "generated_utc": core.now(),
        "process_id": os.getpid(),
        "destination_namespace": core.DEST,
        "asset_mutations": [],
        "editor_bootstrap_world": None,
        "project_maps_loaded_or_saved": [],
        "writes_authorized": [str(receipt), str(failure)],
    }
    package_hashes_before = None
    namespace_before = None
    try:
        evidence["editor_bootstrap_world"] = core.require_engine_entry_bootstrap_world()
        if receipt.exists() or failure.exists():
            raise RuntimeError("current v010 run already contains a validation result")
        baseline, contract, state = load_validation_baseline()
        imported, summary, quarantine = recovery.validate_v009_receipts(state["v009"])
        import_pid = int(imported.get("process_id", -1))
        if import_pid != 36612 or import_pid == os.getpid():
            raise RuntimeError("v010 validator is not distinct from exact v009 import process")
        if core.sha256(
                recovery.V009_RUN / "import_receipt_recovery_v009.json") \
                != recovery.V009_IMPORT_RECEIPT_SHA256:
            raise RuntimeError("preserved v009 import receipt hash drift")

        source_before = core.verify_source(baseline)
        protected_before = core.verify_protected(baseline)
        prepared_lane_before = core.verify_lane(baseline)
        namespace_before = core.namespace_inventory()
        package_hashes_before = core.package_hashes(baseline)
        if (namespace_before != imported.get("namespace_disk_files")
                or package_hashes_before != imported.get("package_sha256")):
            raise RuntimeError("v009 package bytes changed before v010 fresh asset loads")

        registry_before = {
            str(path).rsplit(".", 1)[0]
            for path in core.library.list_assets(
                core.DEST, recursive=True, include_folder=False)
        }
        expected_registry = set(baseline["destination"]["expected_package_paths"])
        if registry_before != expected_registry:
            raise RuntimeError("v010 pre-load asset-registry closure drift")

        measured = core.validate_all_assets(
            baseline, require_persisted_dependencies=True)

        package_hashes_after = core.package_hashes(baseline)
        namespace_after = core.namespace_inventory()
        registry_after = {
            str(path).rsplit(".", 1)[0]
            for path in core.library.list_assets(
                core.DEST, recursive=True, include_folder=False)
        }
        source_after = core.verify_source(baseline)
        protected_after = core.verify_protected(baseline)
        prepared_lane_after = core.verify_lane(baseline)
        if package_hashes_after != package_hashes_before:
            raise RuntimeError("runtime package bytes changed during v010 read-only validation")
        if namespace_after != namespace_before:
            raise RuntimeError("runtime namespace changed during v010 read-only validation")
        if registry_after != registry_before:
            raise RuntimeError("asset-registry closure changed during v010 read-only validation")
        if (source_after != source_before or protected_after != protected_before
                or prepared_lane_after != prepared_lane_before):
            raise RuntimeError("source/protected/prepared lane changed during v010 validation")

        evidence.update({
            "status": VALIDATION_PASS,
            "engine_version": str(unreal.SystemLibrary.get_engine_version()),
            "import_process_id": import_pid,
            "validator_process_id": os.getpid(),
            "distinct_process_verified": True,
            "contract_sha256": baseline["_contract_sha256"],
            "baseline_sha256": baseline["_baseline_sha256"],
            "recovery_contract_sha256": baseline["_recovery_contract_sha256"],
            "v009_recovery_contract_sha256": recovery.V009_CONTRACT_SHA256,
            "v009_import_receipt_sha256": recovery.V009_IMPORT_RECEIPT_SHA256,
            "v009_wrapper_failure_summary_sha256": recovery.V009_SUMMARY_SHA256,
            "v009_quarantine_receipt_sha256": recovery.V009_QUARANTINE_RECEIPT_SHA256,
            "v009_wrapper_failure_classification": contract[
                "completed_v009_import"]["classification"],
            "v009_wrapper_incident_binding_sha256": contract[
                "completed_v009_import"]["binding_sha256"],
            "incident_chain_sha256": contract["incident_chain"]["binding_sha256"],
            "quarantine_receipt": {
                "path": core.relative(
                    recovery.V009_RUN / "quarantine_receipt_v009.json"),
                "bytes": (recovery.V009_RUN / "quarantine_receipt_v009.json").stat().st_size,
                "sha256": recovery.V009_QUARANTINE_RECEIPT_SHA256,
                "status": quarantine["status"],
            },
            "source_before": source_before,
            "source_after": source_after,
            "protected_before": protected_before,
            "protected_after": protected_after,
            "prepared_lane_before": prepared_lane_before,
            "prepared_lane_after": prepared_lane_after,
            "package_sha256_before_loads": package_hashes_before,
            "package_sha256_after_loads": package_hashes_after,
            "namespace_before": namespace_before,
            "namespace_after": namespace_after,
            "asset_registry_packages_before": sorted(
                registry_before, key=str.casefold),
            "asset_registry_packages_after": sorted(
                registry_after, key=str.casefold),
            "assets": measured,
            "mesh_count": 4,
            "authored_lod_count": 12,
            "texture_count": 3,
            "material_count": 4,
            "package_count": 11,
            "all_package_hashes_unchanged": True,
            "persisted_asset_registry_dependency_closure_verified": True,
            "asset_mutation_count": 0,
            "import_or_reimport_process_count": 0,
            "ubt_startup_guard_environment": {
                "name": "UE_SKIP_UBT_SDK_SETUP", "required_value": "1",
                "observed_value": os.environ.get("UE_SKIP_UBT_SDK_SETUP", ""),
            },
            "failures": [],
        })
        if evidence["ubt_startup_guard_environment"]["observed_value"] != "1":
            raise RuntimeError("UE_SKIP_UBT_SDK_SETUP was not inherited as exact value 1")
        core.write_json(receipt, evidence)
        unreal.log(
            "LINE_BOSS_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V010_VALIDATION_PASS")
        print(json.dumps(evidence, indent=2))
    except Exception as error:
        evidence.update({
            "status": (
                "FAIL_CLOSED__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V010_"
                "FRESH_PROCESS_VALIDATION"),
            "error": str(error),
            "traceback": traceback.format_exc(),
            "package_hashes_before": package_hashes_before,
            "namespace_before": namespace_before,
            "v009_import_receipt_sha256": recovery.V009_IMPORT_RECEIPT_SHA256,
            "namespace_preserved_for_recovery": core.namespace_inventory(),
            "automatic_cleanup": "NOT_PERFORMED__READ_ONLY_VALIDATOR",
        })
        core.write_json(failure, evidence)
        unreal.log_error(
            "LINE_BOSS_CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V010_VALIDATION_FAIL: "
            + str(error))
        print(json.dumps(evidence, indent=2))
        raise


if __name__ == "__main__":
    main()
