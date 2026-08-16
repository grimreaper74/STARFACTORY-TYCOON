"""One-process, read-only fresh validation for panel Recovery_v002."""

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
import cairnwell_2040_panel_modules_recovery_v002 as recovery


PASS_STATUS = (
    "PASS__CAIRNWELL_2040_PANEL_MODULES_V001_RECOVERY_V002__"
    "DISTINCT_FRESH_READ_ONLY_RELOAD__11_MESHES__33_AUTHORED_LODS__"
    "EXACT_PERSISTED_RUNTIME_MATERIAL_DEPENDENCIES__11_PANEL_AND_11_RUNTIME_"
    "PACKAGE_HASHES_UNCHANGED"
)


def main() -> None:
    root = recovery.run_root()
    receipt = root / recovery.RECEIPT
    failure = root / recovery.FAILURE
    record = {
        "$schema": (
            "lineboss/audit/cairnwell-2040-panel-modules-v001/"
            "recovery-v002/fresh-process-validation/v2"
        ),
        "generated_utc": recovery.now(),
        "status": None,
        "process_id": os.getpid(),
        "incident_v001_run_id": "20260815T182842Z-0205ac3e",
        "asset_mutations": [],
        "project_maps_loaded_or_saved": [],
        "writes_authorized": [str(receipt), str(failure)],
        "vehicle_model_id": "CAIRNWELL_2040",
        "development_geometry_revisionable": True,
        "final_release_visual_lock_claimed": False,
    }
    package_before = source_before = protected_before = lane_before = None
    runtime_before = cache_before = legacy_before = None
    incidental_before = None
    try:
        bootstrap = lane.require_engine_entry_bootstrap_world()
        contract, contract_digest = recovery.load_contract()
        recovery.verify_result_topology(root)
        command_line = str(unreal.SystemLibrary.get_command_line())
        required_switches = list(contract["recovery"]["required_editor_command_line_tokens"])
        required_switches.extend([
            contract["recovery"]["uncontrolled_changelist_write_suppression_override"],
            contract["recovery"]["python_stub_write_suppression_override"],
            str(Path(__file__).resolve()),
            str(root / "fresh_process_validation_recovery_v002.log"),
        ])
        if (
            os.environ.get("PYTHONDONTWRITEBYTECODE") != "1"
            or any(value.casefold() not in command_line.casefold() for value in required_switches)
        ):
            raise recovery.RecoveryError("read-only startup write-suppression guard drift")
        recovery.verify_incident(contract)
        package_before = recovery.verify_packages(contract)
        incidental_before = recovery.verify_incidental_content(contract)
        if receipt.exists() or failure.exists():
            raise recovery.RecoveryError("Recovery_v002 result already exists")
        if os.getpid() == contract["incident_v001"]["importer_process_id"]:
            raise recovery.RecoveryError("Recovery_v002 did not use a distinct process")

        baseline = lane.load_baseline()
        if (
            baseline["_contract_sha256"]
            != contract["panel_contract"]["payload"]["sha256"]
            or baseline["_baseline_sha256"]
            != contract["panel_baseline_v002"]["payload"]["sha256"]
        ):
            raise recovery.RecoveryError("panel contract/baseline binding drift")
        source_before = lane.verify_source(baseline)
        protected_before = lane.verify_protected(baseline)
        lane_before = lane.verify_lane(baseline)
        runtime_before = lane.verify_runtime(baseline)
        cache_before = lane.asset_registry_cache_snapshot()
        legacy_before = lane.legacy_asset_registry_cache_absence()
        if (
            source_before != contract["baseline_authority"]["source"]
            or protected_before != contract["baseline_authority"]["protected"]
            or lane_before != contract["baseline_authority"]["lane"]
            or runtime_before != contract["baseline_authority"]["runtime"]
            or cache_before != contract["baseline_authority"]["asset_registry_cache"]
            or legacy_before
            != contract["baseline_authority"]["legacy_asset_registry_cache_absence"]
        ):
            raise recovery.RecoveryError("pre-load immutable authority drift")

        registry_before = {
            str(path).rsplit(".", 1)[0]
            for path in lane.library.list_assets(
                lane.DEST, recursive=True, include_folder=False
            )
        }
        expected_registry = set(baseline["destination"]["expected_package_paths"])
        if registry_before != expected_registry:
            raise recovery.RecoveryError("fresh registry does not expose exact 11 packages")

        dependency_options = recovery.install_persisted_dependency_query(lane, unreal)
        measured = lane.validate_all_assets(
            baseline, require_persisted_dependencies=True
        )
        for panel_id in lane.PANEL_IDS:
            panel = measured["panels"][panel_id]
            expected_material = baseline["modules"][panel_id]["material_bindings"][
                "default"
            ].split(".", 1)[0]
            if (
                panel.get("persisted_dependency_check_required") is not True
                or panel.get("persisted_relevant_dependencies") != [expected_material]
            ):
                raise recovery.RecoveryError(
                    "persisted material dependency evidence drift: " + panel_id
                )

        package_after = recovery.verify_packages(contract)
        source_after = lane.verify_source(baseline)
        protected_after = lane.verify_protected(baseline)
        lane_after = lane.verify_lane(baseline)
        runtime_after = lane.verify_runtime(baseline)
        cache_after = lane.asset_registry_cache_snapshot()
        legacy_after = lane.legacy_asset_registry_cache_absence()
        incidental_after = recovery.verify_incidental_content(contract)
        registry_after = {
            str(path).rsplit(".", 1)[0]
            for path in lane.library.list_assets(
                lane.DEST, recursive=True, include_folder=False
            )
        }
        if (
            package_after != package_before
            or source_after != source_before
            or protected_after != protected_before
            or lane_after != lane_before
            or runtime_after != runtime_before
            or cache_after != cache_before
            or legacy_after != legacy_before
            or registry_after != registry_before
        ):
            raise recovery.RecoveryError(
                "read-only validation changed package/project/cache authority"
            )

        record.update({
            "status": PASS_STATUS,
            "engine_version": str(unreal.SystemLibrary.get_engine_version()),
            "editor_bootstrap_world": bootstrap,
            "contract_sha256": contract_digest,
            "panel_contract_sha256": baseline["_contract_sha256"],
            "panel_baseline_v002_sha256": baseline["_baseline_sha256"],
            "incident_v001_files": contract["incident_v001"]["files"],
            "distinct_from_v001_importer_process": True,
            "source_before": source_before,
            "source_after": source_after,
            "protected_before": protected_before,
            "protected_after": protected_after,
            "prepared_lane_before": lane_before,
            "prepared_lane_after": lane_after,
            "runtime_before": runtime_before,
            "runtime_after": runtime_after,
            "asset_registry_cache_before": cache_before,
            "asset_registry_cache_after": cache_after,
            "legacy_asset_registry_cache_absence_before": legacy_before,
            "legacy_asset_registry_cache_absence_after": legacy_after,
            "exact_ten_incidental_files_before": incidental_before,
            "exact_ten_incidental_files_after": incidental_after,
            "panel_package_files_before_loads": package_before,
            "panel_package_files_after_loads": package_after,
            "asset_registry_packages_before": sorted(registry_before, key=str.casefold),
            "asset_registry_packages_after": sorted(registry_after, key=str.casefold),
            "assets": measured,
            "mesh_count": 11,
            "authored_lod_count": 33,
            "package_count": 11,
            "new_texture_count": 0,
            "new_material_count": 0,
            "persisted_runtime_material_dependencies_verified": True,
            "asset_registry_dependency_options": dependency_options,
            "all_panel_package_hashes_unchanged": True,
            "all_runtime_package_hashes_unchanged": True,
            "asset_mutation_count": 0,
            "existing_incidental_file_content_mutation_count": 0,
            "no_asset_registry_cache_write_command_line_verified": True,
            "read_only_startup_write_suppression": {
                "required_switches": required_switches,
                "all_required_switches_observed": True,
                "python_dont_write_bytecode_environment": {
                    "name": "PYTHONDONTWRITEBYTECODE",
                    "observed_value": os.environ.get("PYTHONDONTWRITEBYTECODE"),
                },
            },
            "ubt_startup_guard_environment": {
                "name": "UE_SKIP_UBT_SDK_SETUP",
                "required_value": "1",
                "observed_value": os.environ.get("UE_SKIP_UBT_SDK_SETUP"),
            },
            "failures": [],
        })
        recovery.write_json(receipt, record)
        unreal.log("LINE_BOSS_CAIRNWELL_2040_PANEL_MODULES_RECOVERY_V002_VALIDATION_PASS")
        print(json.dumps(record, indent=2))
    except Exception as error:
        record.update({
            "status": (
                "FAIL_CLOSED__CAIRNWELL_2040_PANEL_MODULES_V001_"
                "RECOVERY_V002_FRESH_PROCESS_VALIDATION"
            ),
            "error": str(error),
            "traceback": traceback.format_exc(),
            "panel_package_files_before": package_before,
            "source_before": source_before,
            "protected_before": protected_before,
            "prepared_lane_before": lane_before,
            "runtime_before": runtime_before,
            "asset_registry_cache_before": cache_before,
            "legacy_asset_registry_cache_absence_before": legacy_before,
            "exact_ten_incidental_files_before": incidental_before,
            "automatic_cleanup": "NOT_PERFORMED__READ_ONLY_VALIDATOR",
        })
        recovery.write_json(failure, record)
        unreal.log_error(
            "LINE_BOSS_CAIRNWELL_2040_PANEL_MODULES_RECOVERY_V002_VALIDATION_FAIL: "
            + str(error)
        )
        print(json.dumps(record, indent=2))
        raise


if __name__ == "__main__":
    main()
