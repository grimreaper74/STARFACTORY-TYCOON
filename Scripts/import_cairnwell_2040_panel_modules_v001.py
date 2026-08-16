"""Fresh-only UE 5.8 importer for the exact 11 Cairnwell panel modules.

The importer creates only 11 StaticMesh packages in the isolated panel
namespace.  It creates zero textures/materials, instead loading the immutable
approved runtime material family.  No project map is loaded or saved, no
existing package is replaced/reimported/deleted, and partial artifacts are
preserved for explicit review if the fail-closed lane aborts.
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


PASS_STATUS = (
    "PASS__CAIRNWELL_2040_PANEL_MODULES_V001_FRESH_IMPORT__"
    "11_MESHES__33_AUTHORED_LODS__ZERO_NEW_TEXTURES_MATERIALS__EXACT_11_PACKAGES"
)


def mesh_task(spec: dict):
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(lane.PROJECT / spec["lods"][0]["source"]["path"]),
        "destination_path": spec["package_path"].rsplit("/", 1)[0],
        "destination_name": spec["asset_name"],
        "automated": True,
        "replace_existing": False,
        "replace_existing_settings": False,
        "save": False,
        "factory": unreal.FbxFactory(),
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True,
        "import_as_skeletal": False,
        "import_materials": False,
        "import_textures": False,
        "import_animations": False,
        "automated_import_should_detect_type": False,
        "create_physics_asset": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    static = options.get_editor_property("static_mesh_import_data")
    static.set_editor_properties({
        "import_uniform_scale": 1.0,
        "convert_scene": True,
        "convert_scene_unit": True,
        "force_front_x_axis": False,
        "transform_vertex_to_absolute": True,
        "bake_pivot_in_vertex": False,
        "generate_lightmap_u_vs": False,
        "auto_generate_collision": False,
        "remove_degenerates": False,
        "combine_meshes": True,
        "build_nanite": False,
    })
    options.set_editor_property("static_mesh_import_data", static)
    task.set_editor_property("options", options)
    return task


def load_runtime_materials(baseline: dict) -> dict:
    materials = {}
    for role, spec in baseline["material_reuse"]["materials"].items():
        material = lane.library.load_asset(spec["object_path"])
        if not isinstance(material, unreal.MaterialInterface) or material.get_path_name() != spec["object_path"]:
            lane.fail("approved runtime material is unavailable: " + role)
        materials[role] = material
    if set(materials) != {"biw_galvanised", "ed_coat", "player_paint"}:
        lane.fail("exact three-role runtime material family is unavailable")
    return materials


def import_lod0(baseline: dict) -> dict:
    tasks = [mesh_task(baseline["modules"][panel_id]) for panel_id in lane.PANEL_IDS]
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    meshes = {}
    for panel_id, task in zip(lane.PANEL_IDS, tasks):
        spec = baseline["modules"][panel_id]
        imported = [str(value) for value in task.get_editor_property("imported_object_paths")]
        if imported != [spec["object_path"]]:
            lane.fail(f"fresh LOD0 import result drift: {panel_id}:{imported}")
        mesh = lane.library.load_asset(spec["package_path"])
        if (
            not isinstance(mesh, unreal.StaticMesh)
            or mesh.get_path_name() != spec["object_path"]
            or int(mesh.get_num_lods()) != 1
        ):
            lane.fail("fresh LOD0 StaticMesh identity/count drift: " + panel_id)
        meshes[panel_id] = mesh
    return meshes


def append_authored_lods(meshes: dict, baseline: dict, subsystem) -> dict:
    previous = int(unreal.SystemLibrary.get_console_variable_int_value(lane.INTERCHANGE_FBX_CVAR))
    evidence = {
        "name": lane.INTERCHANGE_FBX_CVAR,
        "previous_value": previous,
        "disabled_value": None,
        "restored_value": None,
        "custom_lods_requested": 22,
        "custom_lods_imported": [],
        "restore_attempted_in_finally": False,
        "set_false_only_around_custom_lod_imports": True,
    }
    if previous not in (0, 1):
        lane.fail("unexpected Interchange FBX feature-flag value: " + str(previous))
    caught = None
    try:
        unreal.SystemLibrary.execute_console_command(None, lane.INTERCHANGE_FBX_CVAR + " 0")
        evidence["disabled_value"] = int(
            unreal.SystemLibrary.get_console_variable_int_value(lane.INTERCHANGE_FBX_CVAR)
        )
        if evidence["disabled_value"] != 0:
            lane.fail("legacy custom-LOD importer could not be activated")
        for panel_id in lane.PANEL_IDS:
            for lod_index in (1, 2):
                source = lane.PROJECT / baseline["modules"][panel_id]["lods"][lod_index]["source"]["path"]
                imported_lod_index = int(subsystem.import_lod(meshes[panel_id], lod_index, str(source)))
                if imported_lod_index != lod_index:
                    lane.fail(f"authored custom LOD append failed: {panel_id}:LOD{lod_index}")
                evidence["custom_lods_imported"].append({
                    "panel_id": panel_id,
                    "lod": lod_index,
                    "source": lane.relative(source),
                    "source_sha256": lane.sha256(source),
                })
    except Exception as error:
        caught = error
    finally:
        evidence["restore_attempted_in_finally"] = True
        unreal.SystemLibrary.execute_console_command(None, f"{lane.INTERCHANGE_FBX_CVAR} {previous}")
        evidence["restored_value"] = int(
            unreal.SystemLibrary.get_console_variable_int_value(lane.INTERCHANGE_FBX_CVAR)
        )
    if evidence["restored_value"] != previous:
        lane.fail("Interchange FBX feature flag restoration drift")
    if caught is not None:
        raise caught
    if len(evidence["custom_lods_imported"]) != 22:
        lane.fail("authored custom-LOD append count drift")
    return evidence


def configure_mesh(panel_id: str, spec: dict, mesh, default_material, subsystem) -> None:
    if int(mesh.get_num_lods()) != 3:
        lane.fail("expected exactly three authored source models: " + panel_id)
    nanite = subsystem.get_nanite_settings(mesh)
    nanite.set_editor_property("enabled", False)
    subsystem.set_nanite_settings(mesh, nanite, apply_changes=True)
    if (
        int(unreal.EditorStaticMeshLibrary.get_simple_collision_count(mesh)) != 0
        or int(unreal.EditorStaticMeshLibrary.get_convex_collision_count(mesh)) != 0
    ):
        lane.fail("fresh panel unexpectedly contains collision: " + panel_id)
    body = mesh.get_editor_property("body_setup")
    if body is None:
        lane.fail("BodySetup missing: " + panel_id)
    body.set_editor_property(
        "collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX
    )
    mesh.set_editor_property("has_navigation_data", False)
    slots = lane.slot_names(mesh)
    if slots != [lane.SEMANTIC_SLOT]:
        lane.fail("source/import semantic material slot drift: " + panel_id + repr(slots))
    if default_material.get_path_name() != spec["material_bindings"]["default"]:
        lane.fail("default solid-colour runtime material authority drift")
    mesh.set_material(0, default_material)
    if not lane.library.save_loaded_asset(mesh, only_if_is_dirty=False):
        lane.fail("configured panel mesh save failed: " + panel_id)


def persist_manual_screens(meshes: dict, baseline: dict, subsystem) -> dict:
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    wanted = [float(value) for value in baseline["import_contract"]["lod_screen_sizes"]]
    rounded = [round(value, 6) for value in wanted]
    evidence = {panel_id: [] for panel_id in lane.PANEL_IDS}
    for pass_index in (1, 2):
        if pass_index == 2:
            unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        for panel_id in lane.PANEL_IDS:
            mesh = meshes[panel_id]
            if not subsystem.set_lod_screen_sizes(mesh, wanted):
                lane.fail(f"manual screen-size pass {pass_index} failed: {panel_id}")
            readback = [round(float(value), 6) for value in subsystem.get_lod_screen_sizes(mesh)]
            automatic = bool(mesh.is_lod_screen_size_auto_computed())
            if readback != rounded or automatic:
                lane.fail(f"manual screen-size pass {pass_index} drift: {panel_id}")
            if not lane.library.save_loaded_asset(mesh, only_if_is_dirty=False):
                lane.fail(f"manual screen-size save failed: {panel_id}")
            evidence[panel_id].append({
                "pass": pass_index,
                "readback": readback,
                "auto_compute": automatic,
            })
    return evidence


def main() -> None:
    root = lane.run_root()
    receipt = root / lane.IMPORT_RECEIPT
    failure = root / lane.IMPORT_FAILURE
    record = {
        "$schema": "lineboss/audit/cairnwell-2040-panel-modules-v001/unreal-import/v1",
        "generated_utc": lane.now(),
        "process_id": os.getpid(),
        "destination_namespace": lane.DEST,
        "writes_authorized": [str(lane.DEST_DISK), str(root)],
        "editor_bootstrap_world": None,
        "project_maps_loaded_or_saved": [],
        "replace_reimport_delete_operations": [],
        "new_texture_or_material_operations": [],
        "runtime_authority_mutations": [],
        "vehicle_model_id": "CAIRNWELL_2040",
        "production_recipe_id": "CAIRNWELL_2040_DEVELOPMENT_RECIPE_V001",
        "development_geometry_revisionable": True,
        "final_release_visual_lock_claimed": False,
        "no_asset_registry_cache_write_command_line_verified": False,
        "ubt_startup_guard_environment": None,
    }
    source_before = protected_before = prepared_lane_before = runtime_before = None
    cache_before = legacy_cache_before = None
    try:
        record["editor_bootstrap_world"] = lane.require_engine_entry_bootstrap_world()
        if receipt.exists() or failure.exists():
            lane.fail("current run already contains an import result")
        baseline = lane.load_baseline()
        if lane.prior_results():
            lane.fail("lane refuses every pre-existing v001 PASS or FAIL result")
        if lane.DEST_DISK.exists() or lane.library.does_directory_exist(lane.DEST):
            lane.fail("fresh destination already exists; overwrite/reimport forbidden")
        if lane.library.list_assets(lane.DEST, recursive=True, include_folder=False):
            lane.fail("asset registry already exposes the fresh destination")
        for package in baseline["destination"]["expected_package_paths"]:
            if lane.library.does_asset_exist(package):
                lane.fail("fresh panel package already exists: " + package)

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
            lane.fail("pre-import cache surfaces differ from frozen V013/panel baseline")
        materials = load_runtime_materials(baseline)
        meshes = import_lod0(baseline)
        subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        if subsystem is None or not hasattr(subsystem, "import_lod"):
            lane.fail("UE 5.8 StaticMeshEditorSubsystem/custom-LOD API unavailable")
        cvar = append_authored_lods(meshes, baseline, subsystem)
        default_role = baseline["material_reuse"]["default_role"]
        if default_role != "player_paint" or default_role not in materials:
            lane.fail("approved solid-colour player-paint default role drift")
        default_material = materials[default_role]
        for panel_id in lane.PANEL_IDS:
            configure_mesh(
                panel_id, baseline["modules"][panel_id], meshes[panel_id], default_material, subsystem
            )
        screens = persist_manual_screens(meshes, baseline, subsystem)
        measured = lane.validate_all_assets(baseline, require_persisted_dependencies=False)

        registry = {
            str(path).rsplit(".", 1)[0]
            for path in lane.library.list_assets(lane.DEST, recursive=True, include_folder=False)
        }
        if registry != set(baseline["destination"]["expected_package_paths"]):
            lane.fail("exact 11-package panel asset-registry closure drift")
        disk = lane.namespace_inventory()
        expected_disk = {baseline["modules"][panel_id]["disk_path"] for panel_id in lane.PANEL_IDS}
        if set(disk) != expected_disk:
            lane.fail("exact 11-package panel disk inventory drift")
        panel_packages = lane.package_hashes(baseline)

        source_after = lane.verify_source(baseline)
        protected_after = lane.verify_protected(baseline)
        prepared_lane_after = lane.verify_lane(baseline)
        runtime_after = lane.verify_runtime(baseline)
        cache_after = lane.asset_registry_cache_snapshot()
        legacy_cache_after = lane.legacy_asset_registry_cache_absence()
        if (
            source_after != source_before
            or protected_after != protected_before
            or prepared_lane_after != prepared_lane_before
            or runtime_after != runtime_before
            or cache_after != cache_before
            or legacy_cache_after != legacy_cache_before
        ):
            lane.fail("source/protected/lane/runtime/cache authority changed during panel import")
        if int(unreal.SystemLibrary.get_console_variable_int_value(lane.INTERCHANGE_FBX_CVAR)) != int(
            cvar["previous_value"]
        ):
            lane.fail("Interchange FBX feature flag changed after guarded restoration")
        record.update({
            "status": PASS_STATUS,
            "engine_version": str(unreal.SystemLibrary.get_engine_version()),
            "contract_sha256": baseline["_contract_sha256"],
            "baseline_sha256": baseline["_baseline_sha256"],
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
            "runtime_material_reuse": {
                role: material.get_path_name() for role, material in materials.items()
            },
            "panel_package_sha256": panel_packages,
            "assets": measured,
            "mesh_count": 11,
            "authored_lod_count": 33,
            "texture_count": 0,
            "material_count": 0,
            "package_count": 11,
            "strict_lod_uv_clean_edges_bounds_shared_origin_material_gates_verified": True,
            "nanite_collision_navigation_off_verified": True,
            "runtime_packages_unchanged": True,
            "interchange_fbx_legacy_custom_lod_guard": cvar,
            "manual_lod_screen_size_evidence": screens,
            "partial_cleanup": "NOT_PERFORMED",
            "failures": [],
        })
        lane.write_json(receipt, record)
        unreal.log("LINE_BOSS_CAIRNWELL_2040_PANEL_MODULES_V001_IMPORT_PASS")
        print(json.dumps(record, indent=2))
    except Exception as error:
        record.update({
            "status": "FAIL_CLOSED__CAIRNWELL_2040_PANEL_MODULES_V001_IMPORT",
            "error": str(error),
            "traceback": traceback.format_exc(),
            "source_before": source_before,
            "protected_before": protected_before,
            "prepared_lane_before": prepared_lane_before,
            "runtime_before": runtime_before,
            "asset_registry_cache_before": cache_before,
            "legacy_asset_registry_cache_absence_before": legacy_cache_before,
            "destination_preserved_for_recovery": lane.namespace_inventory(),
            "automatic_cleanup": "NOT_PERFORMED__PARTIAL_ARTIFACTS_PRESERVED_FOR_EXPLICIT_REVIEW",
        })
        lane.write_json(failure, record)
        unreal.log_error("LINE_BOSS_CAIRNWELL_2040_PANEL_MODULES_V001_IMPORT_FAIL: " + str(error))
        print(json.dumps(record, indent=2))
        raise


if __name__ == "__main__":
    main()
