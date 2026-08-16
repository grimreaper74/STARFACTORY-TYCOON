"""One-shot UE 5.8 importer for the frozen original-procedural Paint kit."""

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
import paint_line_native_kit_unreal_runtime_v001 as lane


PASS_STATUS = "PASS__HASH_GUARDED_FRESH_IMPORT__7_ASSETS__21_AUTHORED_LODS__PAINT_NATIVE_KIT_V001"


def make_task(spec: dict):
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(lane.PROJECT / spec["lods"][0]["source"]),
        "destination_path": spec["package_path"].rsplit("/", 1)[0],
        "destination_name": spec["asset_name"], "automated": True,
        "replace_existing": False, "replace_existing_settings": False,
        "save": False, "factory": unreal.FbxFactory(),
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True, "import_as_skeletal": False,
        "import_materials": False, "import_textures": False,
        "import_animations": False, "automated_import_should_detect_type": False,
        "create_physics_asset": False, "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    static = options.get_editor_property("static_mesh_import_data")
    static.set_editor_properties({
        "import_uniform_scale": 1.0, "convert_scene": True, "convert_scene_unit": True,
        "force_front_x_axis": False, "transform_vertex_to_absolute": True,
        "bake_pivot_in_vertex": False, "generate_lightmap_u_vs": False,
        "auto_generate_collision": False, "remove_degenerates": False,
        "combine_meshes": True, "build_nanite": False,
    })
    options.set_editor_property("static_mesh_import_data", static)
    task.set_editor_property("options", options)
    return task


def append_custom_lods(meshes: dict, baseline: dict, subsystem) -> dict:
    previous = int(unreal.SystemLibrary.get_console_variable_int_value(lane.INTERCHANGE_FBX_CVAR))
    evidence = {"name": lane.INTERCHANGE_FBX_CVAR, "previous_value": previous,
                "disabled_value": None, "restored_value": None,
                "custom_lods_requested": 14, "custom_lods_imported": [],
                "restore_attempted_in_finally": False,
                "set_false_only_around_custom_lod_imports": True}
    if previous not in (0, 1):
        lane.fail("unexpected legacy FBX CVar value: " + str(previous))
    import_error = None
    try:
        unreal.SystemLibrary.execute_console_command(None, lane.INTERCHANGE_FBX_CVAR + " 0")
        evidence["disabled_value"] = int(unreal.SystemLibrary.get_console_variable_int_value(lane.INTERCHANGE_FBX_CVAR))
        if evidence["disabled_value"] != 0:
            lane.fail("could not activate UE 5.8 legacy FBX custom-LOD importer")
        for key in sorted(meshes):
            for lod_index in (1, 2):
                source = lane.PROJECT / baseline["assets"][key]["lods"][lod_index]["source"]
                if not subsystem.import_lod(meshes[key], lod_index, str(source)):
                    lane.fail(f"authored custom LOD append failed: {key}:LOD{lod_index}")
                evidence["custom_lods_imported"].append({
                    "asset": key, "lod": lod_index, "source": lane.relative(source),
                    "source_sha256": lane.sha256(source)})
    except Exception as error:
        import_error = error
    finally:
        evidence["restore_attempted_in_finally"] = True
        unreal.SystemLibrary.execute_console_command(None, f"{lane.INTERCHANGE_FBX_CVAR} {previous}")
        evidence["restored_value"] = int(unreal.SystemLibrary.get_console_variable_int_value(lane.INTERCHANGE_FBX_CVAR))
    if evidence["restored_value"] != previous:
        lane.fail("legacy FBX custom-LOD CVar restoration drift: " + repr(evidence))
    if import_error is not None:
        raise import_error
    if len(evidence["custom_lods_imported"]) != 14:
        lane.fail("authored custom LOD append count drift")
    return evidence


def configure_mesh(key: str, spec: dict, subsystem, materials: dict, mesh) -> None:
    if int(mesh.get_num_lods()) != 3:
        lane.fail("expected three authored LODs before configuration: " + key)
    nanite = subsystem.get_nanite_settings(mesh)
    nanite.set_editor_property("enabled", False)
    subsystem.set_nanite_settings(mesh, nanite, apply_changes=True)
    body = mesh.get_editor_property("body_setup")
    if body is None:
        lane.fail("BodySetup missing: " + key)
    if (int(unreal.EditorStaticMeshLibrary.get_simple_collision_count(mesh)) != 0 or
            int(unreal.EditorStaticMeshLibrary.get_convex_collision_count(mesh)) != 0):
        lane.fail("fresh mesh unexpectedly contains collision: " + key)
    collision = spec["collision"]
    if collision["mode"] == "AABB_BOX":
        unreal.EditorStaticMeshLibrary.add_simple_collisions(mesh, unreal.ScriptingCollisionShapeType.BOX)
        body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
    elif collision["mode"] == "COMPLEX_AS_SIMPLE":
        body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    else:
        lane.fail("unsupported per-asset collision mode: " + key)
    slots = lane.slot_names(mesh)
    if slots != spec["lods"][0]["material_slots"]:
        lane.fail("LOD0 global material semantics drift: " + key)
    for index, slot in enumerate(slots):
        mesh.set_material(index, materials[slot])
    if not lane.library.save_loaded_asset(mesh, only_if_is_dirty=False):
        lane.fail("configured mesh save failed: " + key)


def persist_manual_screens(meshes: dict, baseline: dict, subsystem) -> dict:
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    wanted = [float(value) for value in baseline["import_contract"]["lod_screen_sizes"]]
    evidence = {key: [] for key in meshes}
    for pass_index in (1, 2):
        if pass_index == 2:
            unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        for key in sorted(meshes):
            mesh = meshes[key]
            if not subsystem.set_lod_screen_sizes(mesh, wanted):
                lane.fail(f"manual screen-size pass {pass_index} failed: {key}")
            readback = [round(float(value), 6) for value in subsystem.get_lod_screen_sizes(mesh)]
            auto = bool(mesh.is_lod_screen_size_auto_computed())
            if readback != wanted or auto:
                lane.fail(f"manual screen-size pass {pass_index} drift: {key}:{readback}:{auto}")
            if not lane.library.save_loaded_asset(mesh, only_if_is_dirty=False):
                lane.fail(f"manual screen-size pass {pass_index} save failed: {key}")
            evidence[key].append({"pass": pass_index, "readback": readback, "auto_compute": auto})
    return evidence


def main() -> None:
    root = lane.run_root()
    receipt, failure = root / lane.IMPORT_RECEIPT, root / lane.IMPORT_FAILURE
    record = {"$schema": "lineboss/audit/paint-native-kit-v001/unreal-import/v1",
              "generated_utc": lane.now(), "process_id": os.getpid(),
              "destination_namespace": lane.DEST, "maps_loaded_or_saved": [],
              "replace_reimport_delete_operations": [], "asset_or_level_deletes": [],
              "writes_authorized": [str(lane.DEST_DISK), str(root)]}
    source_before = protected_before = None
    try:
        if receipt.exists() or failure.exists():
            lane.fail("current run already contains an import result")
        baseline = lane.load_baseline()
        record["baseline_sha256"] = lane.sha256(lane.BASELINE)
        if lane.prior_results():
            lane.fail("lane refuses every pre-existing v001 result (PASS or FAIL)")
        if lane.DEST_DISK.exists() or lane.library.does_directory_exist(lane.DEST):
            lane.fail("target namespace already exists; overwrite/reimport forbidden")
        if lane.library.list_assets(lane.DEST, recursive=True, include_folder=False):
            lane.fail("target namespace already exists in asset registry")
        source_before = lane.verify_source(baseline)
        protected_before = lane.verify_protected(baseline, full_hash=False)
        materials = {}
        for slot, package in baseline["import_contract"]["material_bindings"].items():
            material = lane.library.load_asset(package)
            if not isinstance(material, unreal.MaterialInterface):
                lane.fail("protected native material unavailable: " + package)
            materials[slot] = material
        keys = sorted(baseline["assets"])
        tasks = [make_task(baseline["assets"][key]) for key in keys]
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        meshes = {}
        for key, task in zip(keys, tasks):
            spec = baseline["assets"][key]
            if [str(value) for value in task.get_editor_property("imported_object_paths")] != [spec["object_path"]]:
                lane.fail("fresh LOD0 import result drift: " + key)
            mesh = lane.library.load_asset(spec["package_path"])
            if not isinstance(mesh, unreal.StaticMesh) or int(mesh.get_num_lods()) != 1:
                lane.fail("fresh LOD0 mesh/type/count drift: " + key)
            meshes[key] = mesh
        subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        if subsystem is None:
            lane.fail("StaticMeshEditorSubsystem unavailable")
        cvar = append_custom_lods(meshes, baseline, subsystem)
        for key in keys:
            configure_mesh(key, baseline["assets"][key], subsystem, materials, meshes[key])
        screens = persist_manual_screens(meshes, baseline, subsystem)
        measured = {key: lane.validate_mesh(key, baseline["assets"][key], baseline, subsystem) for key in keys}
        registry = {str(path).rsplit(".", 1)[0] for path in lane.library.list_assets(lane.DEST, recursive=True, include_folder=False)}
        wanted_registry = {spec["package_path"] for spec in baseline["assets"].values()}
        disk, wanted_disk = lane.namespace_inventory(), {spec["disk_path"] for spec in baseline["assets"].values()}
        if registry != wanted_registry or set(disk) != wanted_disk:
            lane.fail("exact seven-package registry/disk inventory drift")
        source_after = lane.verify_source(baseline)
        protected_after = lane.verify_protected(baseline, full_hash=False)
        if source_after != source_before or protected_after != protected_before:
            lane.fail("protected source/project changed during import")
        portal_assets = sorted(key for key, spec in baseline["assets"].items()
                               if spec["source_direction_contract"]["open_end_portals"])
        record.update({"status": PASS_STATUS, "baseline_status": baseline["status"],
                       "source_before": source_before, "source_after": source_after,
                       "protected_before": protected_before, "protected_after": protected_after,
                       "interchange_fbx_legacy_custom_lod_guard": cvar,
                       "manual_screen_size_persistence": screens, "assets": measured,
                       "asset_registry_packages": sorted(registry), "namespace_disk_files": disk,
                       "asset_count": 7, "lod_count_per_asset": 3, "source_fbx_count": 21,
                       "custom_lods_appended": 14, "new_material_or_texture_assets": 0,
                       "strict_per_asset_monotonic_triangles_verified": True,
                       "exact_one_uv_channel_per_lod_verified": True,
                       "per_asset_collision_suitability_verified": True,
                       "open_end_portal_assets": portal_assets,
                       "both_x_end_portals_and_body_skid_rails_clear_by_exact_geometry_collision": True,
                       "black_box_no_robot_no_window_no_side_door_source_contract_verified": True,
                       "failures": [],
                       "automatic_cleanup": "NOT_PERFORMED__PARTIAL_ARTIFACTS_PRESERVED_FOR_EXPLICIT_REVIEW"})
        receipt.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        unreal.log("LINE_BOSS_PAINT_NATIVE_KIT_V001_IMPORT_PASS")
        unreal.SystemLibrary.quit_editor()
    except Exception as error:
        record.update({"status": "FAIL_CLOSED__PAINT_NATIVE_KIT_V001_UNREAL_IMPORT",
                       "error": str(error), "traceback": traceback.format_exc(),
                       "source_before": source_before, "protected_before": protected_before,
                       "namespace_files_preserved_for_recovery": lane.namespace_inventory(),
                       "automatic_cleanup": "NOT_PERFORMED__PARTIAL_ARTIFACTS_PRESERVED_FOR_EXPLICIT_REVIEW"})
        failure.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        unreal.log_error("LINE_BOSS_PAINT_NATIVE_KIT_V001_IMPORT_FAIL: " + str(error))
        try:
            unreal.SystemLibrary.quit_editor()
        finally:
            raise


if __name__ == "__main__":
    main()
