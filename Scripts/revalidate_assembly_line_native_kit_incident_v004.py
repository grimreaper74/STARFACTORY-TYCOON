"""Independent read-only Assembly v004 validator."""

from __future__ import annotations

import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

import unreal

SCRIPTS = Path(unreal.Paths.project_dir()).resolve() / "Scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import assembly_line_native_kit_incident_retry_runtime_v004 as lane


PASS_STATUS = "PASS__V004_READ_ONLY_RELOAD__CHRONOLOGY_SEPARATED__8_ASSETS_24_LODS"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> None:
    root = lane.run_root()
    receipt, failure = root / lane.PASS_RECEIPT, root / lane.FAIL_RECEIPT
    record = {"$schema": "lineboss/audit/assembly-native-kit-v001/incident-retry-validation/v4",
              "generated_utc": now(), "process_id": os.getpid(),
              "destination_namespace": lane.DEST, "write_scope": [str(receipt), str(failure)],
              "importer_launched": False, "asset_or_level_saves": [], "content_writes": [],
              "imports_reimports_deletes": [], "maps_loaded_or_saved": [],
              "execute_python_path_separator": "/", "historical_hashes_applied_to_live_files": False}
    try:
        if receipt.exists() or failure.exists() or lane.prior_results():
            lane.fail("v004 refuses every prior result (PASS or FAIL)")
        baseline = lane.load_baseline()
        chronology_before = lane.verify_chronology_and_current(baseline)
        source_before = lane.verify_source(baseline)
        protected_before = lane.verify_protected(baseline, full_hash=True)
        target_before = lane.namespace_inventory()
        expected_registry = {spec["package_path"] for spec in baseline["assets"].values()}
        registry = {str(path).rsplit(".", 1)[0]
                    for path in lane.library.list_assets(lane.DEST, recursive=True, include_folder=False)}
        if registry != expected_registry:
            lane.fail("fresh-process asset-registry inventory drift")
        subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        if subsystem is None:
            lane.fail("StaticMeshEditorSubsystem unavailable")
        assets = {key: lane.validate_mesh(key, spec, baseline, subsystem)
                  for key, spec in baseline["assets"].items()}
        target_after = lane.namespace_inventory()
        chronology_after = lane.verify_chronology_and_current(baseline)
        source_after = lane.verify_source(baseline)
        protected_after = lane.verify_protected(baseline, full_hash=True)
        if target_after != target_before:
            lane.fail("read-only reload changed target package bytes/hash/mtime")
        if (chronology_after != chronology_before or source_after != source_before or
                protected_after != protected_before):
            lane.fail("read-only reload changed chronology/current Source/protected authority")
        record.update({"status": PASS_STATUS, "baseline_sha256": lane.sha256(lane.BASELINE),
                       "original_import_receipt": {"path": lane.relative(lane.ORIGINAL_IMPORT_RECEIPT),
                                                   "sha256": lane.EXPECTED_IMPORT_RECEIPT_SHA256},
                       "fresh_process_proof": {
                           "original_import_process_id": chronology_before["original_import_process_id"],
                           "v004_validation_process_id": os.getpid(),
                           "distinct": chronology_before["original_import_process_id"] != os.getpid()},
                       "chronology_before": chronology_before, "chronology_after": chronology_after,
                       "source_before": source_before, "source_after": source_after,
                       "protected_before": protected_before, "protected_after": protected_after,
                       "target_packages_before": target_before, "target_packages_after": target_after,
                       "asset_registry_packages": sorted(registry), "assets": assets,
                       "asset_count": 8, "lod_count_per_asset": 3, "settled_source_file_count": 278,
                       "failed_v002_evidence_file_count": 4, "failed_v003_evidence_file_count": 5,
                       "target_package_hashes_unchanged_by_fresh_load": True,
                       "full_settled_protected_state_unchanged": True,
                       "all_historical_evidence_unchanged": True,
                       "exact_triangles_one_uv_bounds_pivots_material_collision_and_screens_persisted": True,
                       "nanite_off_all_assets": True, "no_content_writes": True,
                       "importer_was_not_launched": True, "failures": []})
        receipt.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        unreal.log("LINE_BOSS_ASSEMBLY_NATIVE_KIT_INCIDENT_RETRY_V004_PASS")
        unreal.SystemLibrary.quit_editor()
    except Exception as error:
        record.update({"status": "FAIL_CLOSED__ASSEMBLY_NATIVE_KIT_INCIDENT_RETRY_V004",
                       "error": str(error), "traceback": traceback.format_exc(),
                       "target_packages_after_failure": lane.namespace_inventory(),
                       "recovery": "Preserve all original/v002/v003 evidence and packages; never rerun v004."})
        failure.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        unreal.log_error("LINE_BOSS_ASSEMBLY_NATIVE_KIT_INCIDENT_RETRY_V004_FAIL: " + str(error))
        try:
            unreal.SystemLibrary.quit_editor()
        finally:
            raise


if __name__ == "__main__":
    main()
