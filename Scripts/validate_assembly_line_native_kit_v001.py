"""Independent fresh-process, read-only validator for Assembly native-kit intake."""

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
import assembly_line_native_kit_unreal_runtime_v001 as lane


EXPECTED_IMPORT_STATUS = "PASS__HASH_GUARDED_FRESH_IMPORT__8_ASSETS__24_AUTHORED_LODS__ASSEMBLY_NATIVE_KIT_V001"
PASS_STATUS = "PASS__INDEPENDENT_FRESH_PROCESS_RELOAD__8_ASSETS__24_AUTHORED_LODS__ASSEMBLY_NATIVE_KIT_V001"


def main() -> None:
    root = lane.run_root()
    import_receipt, import_failure = root / lane.IMPORT_RECEIPT, root / lane.IMPORT_FAILURE
    receipt, failure = root / lane.VALIDATION_RECEIPT, root / lane.VALIDATION_FAILURE
    record = {"$schema": "lineboss/audit/assembly-native-kit-v001/fresh-load-validation/v1",
              "generated_utc": lane.now(), "process_id": os.getpid(),
              "destination_namespace": lane.DEST, "write_scope": [str(receipt), str(failure)],
              "asset_or_level_saves": [], "imports_reimports_deletes": [], "maps_loaded_or_saved": []}
    try:
        if receipt.exists() or failure.exists() or import_failure.exists() or not import_receipt.is_file():
            lane.fail("same-run receipt sequence invalid")
        baseline = lane.load_baseline()
        imported = json.loads(import_receipt.read_text(encoding="utf-8-sig"))
        import_pid = int(imported.get("process_id", -1))
        if (imported.get("$schema") != "lineboss/audit/assembly-native-kit-v001/unreal-import/v1" or
                imported.get("status") != EXPECTED_IMPORT_STATUS or
                imported.get("baseline_sha256") != lane.EXPECTED_BASELINE_SHA256 or
                import_pid <= 0 or import_pid == os.getpid() or imported.get("asset_count") != 8 or
                imported.get("source_fbx_count") != 24 or imported.get("custom_lods_appended") != 16):
            lane.fail("same-run import receipt/fresh-process identity drift")
        guard = imported.get("interchange_fbx_legacy_custom_lod_guard", {})
        if (guard.get("custom_lods_requested") != 16 or len(guard.get("custom_lods_imported", [])) != 16 or
                guard.get("restore_attempted_in_finally") is not True or
                guard.get("restored_value") != guard.get("previous_value")):
            lane.fail("import receipt does not prove guarded legacy custom-LOD CVar restoration")
        source_before = lane.verify_source(baseline)
        protected_before = lane.verify_protected(baseline, full_hash=True)
        target_before = lane.namespace_inventory()
        wanted_disk = {spec["disk_path"] for spec in baseline["assets"].values()}
        if set(target_before) != wanted_disk:
            lane.fail("fresh-process target package inventory drift")
        for key, spec in baseline["assets"].items():
            wanted = imported["namespace_disk_files"][spec["disk_path"]]
            if target_before[spec["disk_path"]] != wanted:
                lane.fail("target package hash/metadata drift before fresh load: " + key)
        registry = {str(path).rsplit(".", 1)[0] for path in lane.library.list_assets(lane.DEST, recursive=True, include_folder=False)}
        wanted_registry = {spec["package_path"] for spec in baseline["assets"].values()}
        if registry != wanted_registry:
            lane.fail("fresh-process asset registry inventory drift")
        subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        if subsystem is None:
            lane.fail("StaticMeshEditorSubsystem unavailable")
        assets = {key: lane.validate_mesh(key, spec, baseline, subsystem) for key, spec in baseline["assets"].items()}
        target_after = lane.namespace_inventory()
        source_after = lane.verify_source(baseline)
        protected_after = lane.verify_protected(baseline, full_hash=True)
        if target_after != target_before:
            lane.fail("fresh reload changed target package bytes/hash/mtime")
        if source_after != source_before or protected_after != protected_before:
            lane.fail("fresh reload changed protected source/project")
        record.update({"status": PASS_STATUS, "baseline_sha256": lane.sha256(lane.BASELINE),
                       "import_receipt": {"path": lane.relative(import_receipt),
                                          "sha256": lane.sha256(import_receipt), "status": imported["status"]},
                       "fresh_process_proof": {"import_process_id": import_pid,
                                               "validation_process_id": os.getpid(), "distinct": True},
                       "source_before": source_before, "source_after": source_after,
                       "protected_before": protected_before, "protected_after": protected_after,
                       "target_packages_before": target_before, "target_packages_after": target_after,
                       "asset_registry_packages": sorted(registry), "assets": assets,
                       "asset_count": 8, "lod_count_per_asset": 3,
                       "target_package_hashes_unchanged_by_fresh_load": True,
                       "complete_source_config_savegames_existing_content_and_maps_unchanged": True,
                       "source_manifest_geometry_roundtrip_and_freeze_reverified": True,
                       "manual_lod_screen_sizes_persisted": True,
                       "exact_triangles_one_uv_bounds_pivots_material_semantics_persisted": True,
                       "per_asset_collision_persisted": True, "nanite_off_all_assets": True,
                       "new_material_or_texture_assets": 0, "failures": []})
        receipt.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        unreal.log("LINE_BOSS_ASSEMBLY_NATIVE_KIT_V001_FRESH_LOAD_VALIDATION_PASS")
        unreal.SystemLibrary.quit_editor()
    except Exception as error:
        record.update({"status": "FAIL_CLOSED__ASSEMBLY_NATIVE_KIT_V001_FRESH_LOAD_VALIDATION",
                       "error": str(error), "traceback": traceback.format_exc(),
                       "target_packages_after_failure": lane.namespace_inventory(),
                       "recovery": "Preserve packages and evidence; do not rerun or delete implicitly."})
        failure.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        unreal.log_error("LINE_BOSS_ASSEMBLY_NATIVE_KIT_V001_FRESH_LOAD_VALIDATION_FAIL: " + str(error))
        try:
            unreal.SystemLibrary.quit_editor()
        finally:
            raise


if __name__ == "__main__":
    main()
