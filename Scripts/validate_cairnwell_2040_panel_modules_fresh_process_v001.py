"""Independent read-only fresh-process validator for the 11 panel modules.

This second UnrealEditor process performs no asset mutation.  It reloads every
panel and all three referenced runtime materials from persisted packages,
verifies exact geometry/material/dependency closure and unchanged hashes, and
never loads or saves a project map.
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
import cairnwell_2040_panel_modules_v001 as lane


IMPORT_PASS = (
    "PASS__CAIRNWELL_2040_PANEL_MODULES_V001_FRESH_IMPORT__"
    "11_MESHES__33_AUTHORED_LODS__ZERO_NEW_TEXTURES_MATERIALS__EXACT_11_PACKAGES"
)
VALIDATION_PASS = (
    "PASS__CAIRNWELL_2040_PANEL_MODULES_V001_DISTINCT_FRESH_PROCESS__"
    "READ_ONLY_RELOAD__11_PANEL_PACKAGE_AND_11_RUNTIME_PACKAGE_HASHES_UNCHANGED"
)


def main() -> None:
    root = lane.run_root()
    import_receipt_path = root / lane.IMPORT_RECEIPT
    receipt = root / lane.VALIDATION_RECEIPT
    failure = root / lane.VALIDATION_FAILURE
    evidence = {
        "$schema": "lineboss/audit/cairnwell-2040-panel-modules-v001/fresh-process-validation/v1",
        "generated_utc": lane.now(),
        "process_id": os.getpid(),
        "destination_namespace": lane.DEST,
        "asset_mutations": [],
        "editor_bootstrap_world": None,
        "project_maps_loaded_or_saved": [],
        "writes_authorized": [str(receipt), str(failure)],
        "vehicle_model_id": "CAIRNWELL_2040",
        "production_recipe_id": "CAIRNWELL_2040_DEVELOPMENT_RECIPE_V001",
        "development_geometry_revisionable": True,
        "final_release_visual_lock_claimed": False,
    }
    panel_hashes_before = namespace_before = runtime_before = None
    cache_before = legacy_cache_before = None
    try:
        evidence["editor_bootstrap_world"] = lane.require_engine_entry_bootstrap_world()
        if receipt.exists() or failure.exists():
            lane.fail("current run already contains a fresh-process result")
        if not import_receipt_path.is_file():
            lane.fail("successful first-process panel import receipt is absent")
        imported = lane.strict_json(import_receipt_path, "panel import receipt")
        if (
            imported.get("status") != IMPORT_PASS
            or imported.get("destination_namespace") != lane.DEST
            or int(imported.get("mesh_count", -1)) != 11
            or int(imported.get("authored_lod_count", -1)) != 33
            or int(imported.get("texture_count", -1)) != 0
            or int(imported.get("material_count", -1)) != 0
            or int(imported.get("package_count", -1)) != 11
            or imported.get("editor_bootstrap_world") != "/Engine/Maps/Entry.Entry"
            or imported.get("project_maps_loaded_or_saved") != []
            or imported.get("runtime_packages_unchanged") is not True
        ):
            lane.fail("first-process panel import receipt identity/count/safety drift")
        import_pid = int(imported.get("process_id", -1))
        if import_pid <= 0 or import_pid == os.getpid():
            lane.fail("validator did not run in a distinct process")
        baseline = lane.load_baseline()
        if (
            imported.get("contract_sha256") != baseline["_contract_sha256"]
            or imported.get("baseline_sha256") != baseline["_baseline_sha256"]
        ):
            lane.fail("first-process receipt contract/baseline hash drift")
        if lane.prior_results() != [lane.relative(import_receipt_path)]:
            lane.fail("fresh-process entry result inventory drift")

        source_before = lane.verify_source(baseline)
        protected_before = lane.verify_protected(baseline)
        prepared_lane_before = lane.verify_lane(baseline)
        runtime_before = lane.verify_runtime(baseline)
        cache_before = lane.asset_registry_cache_snapshot()
        legacy_cache_before = lane.legacy_asset_registry_cache_absence()
        if (
            cache_before != baseline["asset_registry_cache"]
            or legacy_cache_before != baseline["legacy_asset_registry_cache_absence"]
        ):
            lane.fail("fresh-process cache surfaces differ from frozen baseline")
        namespace_before = lane.namespace_inventory()
        panel_hashes_before = lane.package_hashes(baseline)
        if panel_hashes_before != imported.get("panel_package_sha256"):
            lane.fail("panel package bytes changed before independent loads")
        if runtime_before != imported.get("runtime_after"):
            lane.fail("runtime authority changed after first-process exit")
        registry_before = {
            str(path).rsplit(".", 1)[0]
            for path in lane.library.list_assets(lane.DEST, recursive=True, include_folder=False)
        }
        if registry_before != set(baseline["destination"]["expected_package_paths"]):
            lane.fail("fresh-process panel registry closure drift before loads")

        measured = lane.validate_all_assets(baseline, require_persisted_dependencies=True)

        panel_hashes_after = lane.package_hashes(baseline)
        namespace_after = lane.namespace_inventory()
        runtime_after = lane.verify_runtime(baseline)
        cache_after = lane.asset_registry_cache_snapshot()
        legacy_cache_after = lane.legacy_asset_registry_cache_absence()
        registry_after = {
            str(path).rsplit(".", 1)[0]
            for path in lane.library.list_assets(lane.DEST, recursive=True, include_folder=False)
        }
        source_after = lane.verify_source(baseline)
        protected_after = lane.verify_protected(baseline)
        prepared_lane_after = lane.verify_lane(baseline)
        if panel_hashes_after != panel_hashes_before or namespace_after != namespace_before:
            lane.fail("panel package bytes/namespace changed during read-only validation")
        if runtime_after != runtime_before:
            lane.fail("approved runtime authority changed during read-only validation")
        if cache_after != cache_before or legacy_cache_after != legacy_cache_before:
            lane.fail("asset-registry cache surfaces changed during read-only validation")
        if registry_after != registry_before:
            lane.fail("panel asset registry changed during read-only validation")
        if (
            source_after != source_before
            or protected_after != protected_before
            or prepared_lane_after != prepared_lane_before
        ):
            lane.fail("source/protected/lane changed during read-only validation")

        evidence.update({
            "status": VALIDATION_PASS,
            "engine_version": str(unreal.SystemLibrary.get_engine_version()),
            "import_process_id": import_pid,
            "validator_process_id": os.getpid(),
            "distinct_process_verified": True,
            "contract_sha256": baseline["_contract_sha256"],
            "baseline_sha256": baseline["_baseline_sha256"],
            "import_receipt_sha256": lane.sha256(import_receipt_path),
            "source_before": source_before,
            "source_after": source_after,
            "protected_before": protected_before,
            "protected_after": protected_after,
            "prepared_lane_before": prepared_lane_before,
            "prepared_lane_after": prepared_lane_after,
            "runtime_before": runtime_before,
            "runtime_after": runtime_after,
            "asset_registry_cache_before": cache_before,
            "asset_registry_cache_after": cache_after,
            "asset_registry_cache_mutation_count": 0,
            "legacy_asset_registry_cache_absence_before": legacy_cache_before,
            "legacy_asset_registry_cache_absence_after": legacy_cache_after,
            "legacy_asset_registry_cache_mutation_count": 0,
            "no_asset_registry_cache_write_command_line_verified": True,
            "ubt_startup_guard_environment": {
                "name": "UE_SKIP_UBT_SDK_SETUP",
                "required_value": "1",
                "observed_value": os.environ.get("UE_SKIP_UBT_SDK_SETUP"),
            },
            "panel_package_sha256_before_loads": panel_hashes_before,
            "panel_package_sha256_after_loads": panel_hashes_after,
            "namespace_before": namespace_before,
            "namespace_after": namespace_after,
            "asset_registry_packages_before": sorted(registry_before, key=str.casefold),
            "asset_registry_packages_after": sorted(registry_after, key=str.casefold),
            "assets": measured,
            "mesh_count": 11,
            "authored_lod_count": 33,
            "texture_count": 0,
            "material_count": 0,
            "package_count": 11,
            "all_panel_package_hashes_unchanged": True,
            "all_runtime_package_hashes_unchanged": True,
            "persisted_runtime_material_dependencies_verified": True,
            "asset_mutation_count": 0,
            "failures": [],
        })
        lane.write_json(receipt, evidence)
        unreal.log("LINE_BOSS_CAIRNWELL_2040_PANEL_MODULES_V001_FRESH_VALIDATION_PASS")
        print(json.dumps(evidence, indent=2))
    except Exception as error:
        evidence.update({
            "status": "FAIL_CLOSED__CAIRNWELL_2040_PANEL_MODULES_V001_FRESH_PROCESS_VALIDATION",
            "error": str(error),
            "traceback": traceback.format_exc(),
            "panel_hashes_before": panel_hashes_before,
            "namespace_before": namespace_before,
            "runtime_before": runtime_before,
            "asset_registry_cache_before": cache_before,
            "legacy_asset_registry_cache_absence_before": legacy_cache_before,
            "namespace_preserved_for_recovery": lane.namespace_inventory(),
            "automatic_cleanup": "NOT_PERFORMED__READ_ONLY_VALIDATOR",
        })
        lane.write_json(failure, evidence)
        unreal.log_error(
            "LINE_BOSS_CAIRNWELL_2040_PANEL_MODULES_V001_FRESH_VALIDATION_FAIL: "
            + str(error)
        )
        print(json.dumps(evidence, indent=2))
        raise


if __name__ == "__main__":
    main()
