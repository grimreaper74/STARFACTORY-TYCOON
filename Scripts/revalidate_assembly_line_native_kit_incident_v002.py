"""Independent read-only fresh-load recovery validator; imports/saves nothing."""

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
import assembly_line_native_kit_incident_recovery_runtime_v002 as lane


PASS_STATUS = "PASS__INCIDENT_BOUND_INDEPENDENT_FRESH_RELOAD__EXISTING_8_ASSETS_24_LODS__NO_CONTENT_WRITES"


def main() -> None:
    root = lane.run_root()
    receipt, failure = root / lane.PASS_RECEIPT, root / lane.FAIL_RECEIPT
    record = {"$schema": "lineboss/audit/assembly-native-kit-v001/incident-recovery-validation/v2",
              "generated_utc": original_now(), "process_id": os.getpid(),
              "destination_namespace": lane.DEST, "write_scope": [str(receipt), str(failure)],
              "importer_launched": False, "asset_or_level_saves": [], "content_writes": [],
              "imports_reimports_deletes": [], "maps_loaded_or_saved": []}
    try:
        if receipt.exists() or failure.exists() or lane.prior_results():
            lane.fail("successor recovery v002 refuses every prior result (PASS or FAIL)")
        baseline = lane.load_baseline()
        incident_before = lane.verify_incident(baseline)
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
        incident_after = lane.verify_incident(baseline)
        source_after = lane.verify_source(baseline)
        protected_after = lane.verify_protected(baseline, full_hash=True)
        if target_after != target_before:
            lane.fail("fresh read-only reload changed imported package bytes/hash/mtime")
        if incident_after != incident_before or source_after != source_before or protected_after != protected_before:
            lane.fail("fresh read-only reload changed incident/source/protected authority")
        record.update({"status": PASS_STATUS, "baseline_sha256": lane.sha256(lane.BASELINE),
                       "original_import_receipt": {"path": lane.relative(lane.ORIGINAL_IMPORT_RECEIPT),
                                                   "sha256": lane.EXPECTED_IMPORT_RECEIPT_SHA256},
                       "fresh_process_proof": {"original_import_process_id": incident_before["original_import_process_id"],
                                               "recovery_validation_process_id": os.getpid(),
                                               "distinct": incident_before["original_import_process_id"] != os.getpid()},
                       "incident_before": incident_before, "incident_after": incident_after,
                       "source_before": source_before, "source_after": source_after,
                       "protected_before": protected_before, "protected_after": protected_after,
                       "target_packages_before": target_before, "target_packages_after": target_after,
                       "asset_registry_packages": sorted(registry), "assets": assets,
                       "asset_count": 8, "lod_count_per_asset": 3,
                       "settled_source_file_count": 278, "exact_incident_addition_count": 2,
                       "target_package_hashes_unchanged_by_fresh_load": True,
                       "full_settled_protected_state_unchanged": True,
                       "original_baseline_run_receipts_and_logs_unchanged": True,
                       "source_manifest_geometry_roundtrip_and_freeze_reverified": True,
                       "exact_triangles_one_uv_bounds_pivots_material_collision_and_screens_persisted": True,
                       "nanite_off_all_assets": True, "no_content_writes": True,
                       "importer_was_not_launched": True, "failures": []})
        receipt.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        unreal.log("LINE_BOSS_ASSEMBLY_NATIVE_KIT_INCIDENT_RECOVERY_V002_PASS")
        unreal.SystemLibrary.quit_editor()
    except Exception as error:
        record.update({"status": "FAIL_CLOSED__ASSEMBLY_NATIVE_KIT_INCIDENT_RECOVERY_V002",
                       "error": str(error), "traceback": traceback.format_exc(),
                       "target_packages_after_failure": lane.namespace_inventory(),
                       "recovery": "Preserve original packages/run and this evidence; never rerun recovery v002."})
        failure.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        unreal.log_error("LINE_BOSS_ASSEMBLY_NATIVE_KIT_INCIDENT_RECOVERY_V002_FAIL: " + str(error))
        try:
            unreal.SystemLibrary.quit_editor()
        finally:
            raise


def original_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    main()
