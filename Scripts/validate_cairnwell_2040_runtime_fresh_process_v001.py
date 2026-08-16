"""Read-only fresh-process validator for Cairnwell2040Runtime_v001.

This is the second UnrealEditor process in the guarded lane.  It must never
create, import, modify, save, rename, reimport, or remove any Unreal asset.
It bootstraps only immutable /Engine/Maps/Entry and never loads or saves a
project map.
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path

import unreal


SCRIPTS = Path(unreal.Paths.project_dir()).resolve() / "Scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import cairnwell_2040_runtime_v001 as lane


IMPORT_PASS = (
    "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_FRESH_IMPORT__4_MESHES__"
    "12_AUTHORED_LODS__3_TEXTURES__4_MATERIALS__EXACT_11_PACKAGE_CLOSURE"
)
VALIDATION_PASS = (
    "PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_DISTINCT_FRESH_PROCESS__"
    "READ_ONLY_RELOAD__11_PACKAGE_HASHES_UNCHANGED"
)


def main() -> None:
    root = lane.run_root()
    import_receipt_path = root / lane.IMPORT_RECEIPT
    receipt = root / lane.VALIDATION_RECEIPT
    failure = root / lane.VALIDATION_FAILURE
    evidence = {
        "$schema": (
            "lineboss/audit/cairnwell-2040-runtime-v001/"
            "recovery-v009/fresh-process-validation/v9"),
        "generated_utc": lane.now(),
        "process_id": os.getpid(),
        "destination_namespace": lane.DEST,
        "asset_mutations": [],
        "editor_bootstrap_world": None,
        "project_maps_loaded_or_saved": [],
        "writes_authorized": [str(receipt), str(failure)],
    }
    package_hashes_before = None
    namespace_before = None
    quarantine_receipt = None
    try:
        evidence["editor_bootstrap_world"] = lane.require_engine_entry_bootstrap_world()
        if receipt.exists() or failure.exists():
            lane.fail("current run already contains a fresh-process result")
        if not import_receipt_path.is_file():
            lane.fail("successful first-process import receipt is absent")
        import_receipt = json.loads(import_receipt_path.read_text(encoding="utf-8"))
        if (import_receipt.get("$schema")
                != ("lineboss/audit/cairnwell-2040-runtime-v001/"
                    "recovery-v009/unreal-import/v9")
                or import_receipt.get("status") != IMPORT_PASS
                or import_receipt.get("destination_namespace") != lane.DEST
                or int(import_receipt.get("mesh_count", -1)) != 4
                or int(import_receipt.get("authored_lod_count", -1)) != 12
                or int(import_receipt.get("texture_count", -1)) != 3
                or int(import_receipt.get("material_count", -1)) != 4
                or int(import_receipt.get("package_count", -1)) != 11
                or import_receipt.get("editor_bootstrap_world")
                != "/Engine/Maps/Entry.Entry"
                or import_receipt.get("project_maps_loaded_or_saved") != []):
            lane.fail("first-process import receipt identity/count drift")
        import_pid = int(import_receipt.get("process_id", -1))
        if import_pid <= 0 or import_pid == os.getpid():
            lane.fail("fresh validator did not run in a distinct process")

        baseline = lane.load_baseline()
        quarantine_receipt = lane.require_quarantine_receipt(
            baseline["_recovery"], baseline["_recovery_contract_sha256"])
        if (import_receipt.get("contract_sha256") != baseline["_contract_sha256"]
                or import_receipt.get("baseline_sha256") != baseline["_baseline_sha256"]
                or import_receipt.get("recovery_contract_sha256")
                != baseline["_recovery_contract_sha256"]
                or import_receipt.get("v001_failed_run_id")
                != lane.EXPECTED_V001_FAILED_RUN_ID
                or import_receipt.get("v001_import_failure_sha256")
                != lane.EXPECTED_V001_IMPORT_FAILURE_SHA256
                or import_receipt.get("v002_failed_run_id")
                != lane.EXPECTED_V002_FAILED_RUN_ID
                or import_receipt.get("v002_import_failure_sha256")
                != lane.EXPECTED_V002_IMPORT_FAILURE_SHA256
                or import_receipt.get("v003_failed_run_id")
                != lane.EXPECTED_V003_FAILED_RUN_ID
                or import_receipt.get("v003_import_failure_sha256")
                != lane.EXPECTED_V003_IMPORT_FAILURE_SHA256
                or import_receipt.get("v004_failed_run_id")
                != lane.EXPECTED_V004_FAILED_RUN_ID
                or import_receipt.get("v004_import_failure_sha256")
                != lane.EXPECTED_V004_IMPORT_FAILURE_SHA256
                or import_receipt.get("v005_failed_run_id")
                != lane.EXPECTED_V005_FAILED_RUN_ID
                or import_receipt.get("v005_import_failure_sha256")
                != lane.EXPECTED_V005_IMPORT_FAILURE_SHA256
                or import_receipt.get("v006_failed_run_id")
                != lane.EXPECTED_V006_FAILED_RUN_ID
                or import_receipt.get("v006_import_failure_sha256")
                != lane.EXPECTED_V006_IMPORT_FAILURE_SHA256
                or import_receipt.get("incident_chain_sha256")
                != baseline["_recovery"]["incident_chain"]["binding_sha256"]
                or import_receipt.get("quarantine_receipt") != quarantine_receipt):
            lane.fail("first-process receipt contract/baseline/recovery binding drift")
        prior = lane.prior_results()
        expected_prior = [lane.relative(import_receipt_path)]
        if prior != expected_prior:
            lane.fail("fresh-process entry result inventory drift: " + repr(prior))

        source_before = lane.verify_source(baseline)
        protected_before = lane.verify_protected(baseline)
        prepared_lane_before = lane.verify_lane(baseline)
        namespace_before = lane.namespace_inventory()
        package_hashes_before = lane.package_hashes(baseline)
        if package_hashes_before != import_receipt.get("package_sha256"):
            lane.fail("package bytes changed before fresh-process asset loads")

        registry_before = {
            str(path).rsplit(".", 1)[0]
            for path in lane.library.list_assets(lane.DEST, recursive=True, include_folder=False)
        }
        expected_registry = set(baseline["destination"]["expected_package_paths"])
        if registry_before != expected_registry:
            lane.fail("fresh-process asset-registry closure drift before loads")

        measured = lane.validate_all_assets(
            baseline, require_persisted_dependencies=True)

        package_hashes_after = lane.package_hashes(baseline)
        namespace_after = lane.namespace_inventory()
        registry_after = {
            str(path).rsplit(".", 1)[0]
            for path in lane.library.list_assets(lane.DEST, recursive=True, include_folder=False)
        }
        source_after = lane.verify_source(baseline)
        protected_after = lane.verify_protected(baseline)
        prepared_lane_after = lane.verify_lane(baseline)
        if package_hashes_after != package_hashes_before:
            lane.fail("runtime package bytes changed during read-only fresh validation")
        if namespace_after != namespace_before:
            lane.fail("runtime namespace changed during read-only fresh validation")
        if registry_after != registry_before:
            lane.fail("asset-registry closure changed during read-only fresh validation")
        if (source_after != source_before or protected_after != protected_before
                or prepared_lane_after != prepared_lane_before):
            lane.fail("source, protected project, or prepared lane changed during validation")

        evidence.update({
            "status": VALIDATION_PASS,
            "engine_version": str(unreal.SystemLibrary.get_engine_version()),
            "import_process_id": import_pid,
            "validator_process_id": os.getpid(),
            "distinct_process_verified": True,
            "contract_sha256": baseline["_contract_sha256"],
            "baseline_sha256": baseline["_baseline_sha256"],
            "recovery_contract_sha256": baseline["_recovery_contract_sha256"],
            "v001_failed_run_id": lane.EXPECTED_V001_FAILED_RUN_ID,
            "v001_import_failure_sha256": lane.EXPECTED_V001_IMPORT_FAILURE_SHA256,
            "v002_failed_run_id": lane.EXPECTED_V002_FAILED_RUN_ID,
            "v002_import_failure_sha256": lane.EXPECTED_V002_IMPORT_FAILURE_SHA256,
            "v003_failed_run_id": lane.EXPECTED_V003_FAILED_RUN_ID,
            "v003_import_failure_sha256": lane.EXPECTED_V003_IMPORT_FAILURE_SHA256,
            "v004_failed_run_id": lane.EXPECTED_V004_FAILED_RUN_ID,
            "v004_import_failure_sha256": lane.EXPECTED_V004_IMPORT_FAILURE_SHA256,
            "v005_failed_run_id": lane.EXPECTED_V005_FAILED_RUN_ID,
            "v005_import_failure_sha256": lane.EXPECTED_V005_IMPORT_FAILURE_SHA256,
            "v006_failed_run_id": lane.EXPECTED_V006_FAILED_RUN_ID,
            "v006_import_failure_sha256": lane.EXPECTED_V006_IMPORT_FAILURE_SHA256,
            "incident_chain_sha256": baseline["_recovery"]["incident_chain"]["binding_sha256"],
            "quarantine_receipt": quarantine_receipt,
            "import_receipt_sha256": lane.sha256(import_receipt_path),
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
            "asset_registry_packages_before": sorted(registry_before, key=str.casefold),
            "asset_registry_packages_after": sorted(registry_after, key=str.casefold),
            "assets": measured,
            "mesh_count": 4,
            "authored_lod_count": 12,
            "texture_count": 3,
            "material_count": 4,
            "package_count": 11,
            "all_package_hashes_unchanged": True,
            "persisted_asset_registry_dependency_closure_verified": True,
            "asset_mutation_count": 0,
            "failures": [],
        })
        lane.write_json(receipt, evidence)
        unreal.log("LINE_BOSS_CAIRNWELL_2040_RUNTIME_V001_FRESH_PROCESS_VALIDATION_PASS")
        print(json.dumps(evidence, indent=2))
    except Exception as error:
        evidence.update({
            "status": (
                "FAIL_CLOSED__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_"
                "FRESH_PROCESS_VALIDATION"),
            "error": str(error),
            "traceback": traceback.format_exc(),
            "package_hashes_before": package_hashes_before,
            "namespace_before": namespace_before,
            "v001_failed_run_id": lane.EXPECTED_V001_FAILED_RUN_ID,
            "v001_import_failure_sha256": lane.EXPECTED_V001_IMPORT_FAILURE_SHA256,
            "v002_failed_run_id": lane.EXPECTED_V002_FAILED_RUN_ID,
            "v002_import_failure_sha256": lane.EXPECTED_V002_IMPORT_FAILURE_SHA256,
            "v003_failed_run_id": lane.EXPECTED_V003_FAILED_RUN_ID,
            "v003_import_failure_sha256": lane.EXPECTED_V003_IMPORT_FAILURE_SHA256,
            "v004_failed_run_id": lane.EXPECTED_V004_FAILED_RUN_ID,
            "v004_import_failure_sha256": lane.EXPECTED_V004_IMPORT_FAILURE_SHA256,
            "v005_failed_run_id": lane.EXPECTED_V005_FAILED_RUN_ID,
            "v005_import_failure_sha256": lane.EXPECTED_V005_IMPORT_FAILURE_SHA256,
            "v006_failed_run_id": lane.EXPECTED_V006_FAILED_RUN_ID,
            "v006_import_failure_sha256": lane.EXPECTED_V006_IMPORT_FAILURE_SHA256,
            "incident_chain_sha256": (
                baseline["_recovery"]["incident_chain"]["binding_sha256"]
                if "baseline" in locals() else None),
            "quarantine_receipt": quarantine_receipt,
            "namespace_preserved_for_recovery": lane.namespace_inventory(),
            "automatic_cleanup": "NOT_PERFORMED__READ_ONLY_VALIDATOR",
        })
        lane.write_json(failure, evidence)
        unreal.log_error(
            "LINE_BOSS_CAIRNWELL_2040_RUNTIME_V001_FRESH_PROCESS_VALIDATION_FAIL: "
            + str(error))
        print(json.dumps(evidence, indent=2))
        raise


if __name__ == "__main__":
    main()
