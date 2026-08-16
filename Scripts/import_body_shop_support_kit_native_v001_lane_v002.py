"""One-shot UE 5.8 intake for the frozen native Body Shop support kit.

Run only through ``run_body_shop_support_kit_native_unreal_import_lane_v002.ps1``.
The script creates exactly twelve StaticMesh packages below a pristine isolated
candidate namespace.  It never loads/saves a map, changes runtime bindings, or
deletes/replaces any asset.  Partial output is deliberately preserved on error.
"""

from __future__ import annotations

import hashlib
import json
import os
import traceback
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
EXPECTED_PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8").resolve()
BASELINE = PROJECT / "Scripts/body_shop_support_kit_native_unreal_import_baseline_v002.json"
EXPECTED_BASELINE_SHA256 = "E563879DC47887E5F99C9E7DD5D77308F080E6B0A7ECA2C185439669376A5915"
EXPECTED_BASELINE_STATUS = "FROZEN__BODYSHOP_SUPPORT_KIT_NATIVE_V001_UNREAL_IMPORT_BASELINE_V002"
DEST = "/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v001"
DEST_DISK = PROJECT / "Content/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v001"
AUDIT_ROOT = PROJECT / "Saved/Audits/BodyShop/SupportKitNative_v001/UnrealImportLane_v002"
RUN_ROOT_ENV = "LINEBOSS_BS_SUPPORT_KIT_NATIVE_V002_RUN_ROOT"
ACK_ENV = "LINEBOSS_BS_SUPPORT_KIT_NATIVE_V002_ACK"
ACK_TOKEN = "IMPORT_FROZEN_BODYSHOP_SUPPORT_KIT_NATIVE_V001_BASELINE_V002_ONCE"
IMPORT_RECEIPT_NAME = "import_receipt_v002.json"
IMPORT_FAILURE_NAME = "import_failure_v002.json"
INTERCHANGE_FBX_CVAR = "Interchange.FeatureFlags.Import.FBX"
RESULT_NAMES = {
    IMPORT_RECEIPT_NAME,
    IMPORT_FAILURE_NAME,
    "fresh_load_validation_receipt_v002.json",
    "fresh_load_validation_failure_v002.json",
    "lane_summary_v002.json",
}

library = unreal.EditorAssetLibrary


def fail(message: str) -> None:
    raise RuntimeError("BODYSHOP_SUPPORT_KIT_NATIVE_UNREAL_IMPORT_LANE_V002_FAIL: " + message)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest().upper()


def is_inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def project_relative(path: Path) -> str:
    return path.resolve().relative_to(PROJECT).as_posix()


def file_row(path: Path) -> dict:
    if not path.is_file():
        fail("required file is missing: " + str(path))
    stat = path.stat()
    return {
        "path": project_relative(path),
        "bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": sha256(path),
    }


def canonical_inventory_hash(rows: list[dict]) -> str:
    canonical = [
        {
            "path": row["path"],
            "bytes": int(row["bytes"]),
            "mtime_ns": int(row["mtime_ns"]),
            "sha256": row["sha256"],
        }
        for row in sorted(rows, key=lambda item: item["path"].casefold())
    ]
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


def resolve_run_root() -> Path:
    raw = os.environ.get(RUN_ROOT_ENV, "").strip()
    if not raw:
        fail(f"{RUN_ROOT_ENV} is unset; use the guarded PowerShell lane")
    if os.environ.get(ACK_ENV, "").strip() != ACK_TOKEN:
        fail("exact one-shot acknowledgement is absent")
    run_root = Path(raw).resolve()
    if run_root == AUDIT_ROOT.resolve() or not is_inside(run_root, AUDIT_ROOT):
        fail("run directory escapes the dedicated audit root: " + str(run_root))
    if not run_root.is_dir():
        fail("runner-created audit directory is missing: " + str(run_root))
    return run_root


def load_baseline() -> dict:
    if PROJECT != EXPECTED_PROJECT:
        fail(f"project identity drift: {PROJECT} != {EXPECTED_PROJECT}")
    if str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory":
        fail("running game-name drift")
    if Path(unreal.Paths.project_content_dir()).resolve() != (PROJECT / "Content").resolve():
        fail("running project Content path drift")
    if not BASELINE.is_file() or sha256(BASELINE) != EXPECTED_BASELINE_SHA256:
        fail("exact frozen import baseline is missing or changed")
    payload = json.loads(BASELINE.read_text(encoding="utf-8-sig"))
    if (payload.get("$schema") != "lineboss/bodyshop-support-kit-native-v001-unreal-import-baseline/v2"
            or payload.get("status") != EXPECTED_BASELINE_STATUS
            or payload.get("destination", {}).get("namespace") != DEST
            or int(payload.get("destination", {}).get("expected_asset_count", -1)) != 12
            or int(payload.get("destination", {}).get("expected_lod_count_per_asset", -1)) != 3):
        fail("baseline identity/destination contract drift")
    policy = payload.get("policy", {})
    if (policy.get("replace_existing") is not False
            or policy.get("refuse_any_preexisting_lane_result") is not True
            or policy.get("runtime_binding_placement_or_promotion_authorized") is not False):
        fail("baseline safety policy drift")
    return payload


def verify_source(baseline: dict) -> dict:
    expected_rows = {row["path"]: row for row in baseline["source"]["all_files"]}
    root = PROJECT / baseline["source"]["root"]
    actual_paths = {project_relative(path) for path in root.rglob("*") if path.is_file()}
    if actual_paths != set(expected_rows):
        fail("frozen source path inventory drift")
    rows = []
    for relative in sorted(expected_rows, key=str.casefold):
        actual = file_row(PROJECT / relative)
        wanted = expected_rows[relative]
        if (actual["bytes"] != int(wanted["bytes"])
                or actual["mtime_ns"] != int(wanted["mtime_ns"])
                or actual["sha256"] != str(wanted["sha256"]).upper()):
            fail("frozen source file drift: " + relative)
        rows.append(actual)
    digest = canonical_inventory_hash(rows)
    if digest != baseline["source"]["inventory_sha256"]:
        fail("frozen source canonical inventory hash drift")
    return {"file_count": len(rows), "inventory_sha256": digest}


def scan_protected_group(group: dict) -> set[str]:
    selected: set[Path] = set()
    for relative in group.get("files", []):
        selected.add(PROJECT / relative)
    for relative in group.get("roots", []):
        root = PROJECT / relative
        if not root.is_dir():
            if group.get("allow_empty"):
                continue
            fail("protected root missing: " + str(root))
        selected.update(path for path in root.rglob("*") if path.is_file())
    excludes = [PROJECT / relative for relative in group.get("excludes", [])]
    selected = {
        path for path in selected
        if not any(path.resolve() == excluded.resolve() or is_inside(path, excluded) for excluded in excludes)
    }
    return {project_relative(path) for path in selected}


def critical_protected_paths(baseline: dict) -> set[str]:
    output = set()
    for row in baseline["protected"]["files"]:
        groups = set(row.get("groups", []))
        if groups.intersection({
            "project_descriptor", "complete_source_tree", "complete_config_tree", "campaign_save_games",
            "body_shop_map", "press_v913_map", "restored_press_map", "current_native_robot_packages",
        }):
            output.add(row["path"])
    output.update({
        "Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap",
        "Content/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913.umap",
        "Content/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001.umap",
    })
    for package in baseline["import_contract"]["material_bindings"].values():
        output.add("Content/" + package.removeprefix("/Game/") + ".uasset")
    return output


def verify_protected_metadata_and_critical_hashes(baseline: dict) -> dict:
    protected = baseline["protected"]
    expected = {row["path"]: row for row in protected["files"]}
    actual_union: set[str] = set()
    groups = []
    for group in protected["groups"]:
        actual = scan_protected_group(group)
        wanted = set(group["paths"])
        if actual != wanted:
            fail("protected group path inventory drift: " + group["name"])
        actual_union.update(actual)
        groups.append({"name": group["name"], "file_count": len(actual)})
    if actual_union != set(expected):
        fail("protected union path inventory drift")
    metadata_rows = []
    for relative in sorted(actual_union, key=str.casefold):
        path = PROJECT / relative
        stat = path.stat()
        wanted = expected[relative]
        row = {"path": relative, "bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns}
        if row["bytes"] != int(wanted["bytes"]) or row["mtime_ns"] != int(wanted["mtime_ns"]):
            fail("protected file metadata drift: " + relative)
        metadata_rows.append(row)
    critical_rows = []
    for relative in sorted(critical_protected_paths(baseline), key=str.casefold):
        actual = file_row(PROJECT / relative)
        wanted = expected.get(relative)
        if wanted is None or actual["sha256"] != str(wanted["sha256"]).upper():
            fail("critical protected file hash drift: " + relative)
        critical_rows.append(actual)
    metadata_encoded = json.dumps(metadata_rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "file_count": len(metadata_rows),
        "metadata_sha256": hashlib.sha256(metadata_encoded).hexdigest().upper(),
        "critical_hashed_file_count": len(critical_rows),
        "critical_inventory_sha256": canonical_inventory_hash(critical_rows),
        "groups": groups,
    }


def prior_result_files(run_root: Path) -> list[str]:
    if not AUDIT_ROOT.is_dir():
        return []
    results = []
    for path in AUDIT_ROOT.rglob("*"):
        if path.is_file() and path.name in RESULT_NAMES:
            # During importer entry the current run must not yet contain a result.
            results.append(project_relative(path))
    return sorted(results)


def namespace_disk_inventory() -> dict:
    if not DEST_DISK.is_dir():
        return {}
    output = {}
    for path in sorted(DEST_DISK.rglob("*"), key=lambda item: str(item).casefold()):
        if path.is_file():
            row = file_row(path)
            output[row["path"]] = {
                "bytes": row["bytes"], "mtime_ns": row["mtime_ns"], "sha256": row["sha256"]
            }
    return output


def package_file(package_path: str) -> Path:
    return PROJECT / "Content" / Path(package_path.removeprefix("/Game/")).with_suffix(".uasset")


def object_path(package_path: str) -> str:
    return package_path + "." + package_path.rsplit("/", 1)[-1]


def vector(value) -> list[float]:
    return [float(value.x), float(value.y), float(value.z)]


def lod_bounds(mesh: unreal.StaticMesh, lod_index: int) -> dict:
    dynamic_mesh = unreal.DynamicMesh()
    options = unreal.GeometryScriptCopyMeshFromAssetOptions()
    requested_lod = unreal.GeometryScriptMeshReadLOD()
    requested_lod.set_editor_properties({
        "lod_type": unreal.GeometryScriptLODType.SOURCE_MODEL,
        "lod_index": lod_index,
    })
    dynamic_mesh, outcome = unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(
        mesh, dynamic_mesh, options, requested_lod, False
    )
    if outcome != unreal.GeometryScriptOutcomePins.SUCCESS:
        fail(f"source LOD bounds extraction failed: {mesh.get_name()}:LOD{lod_index}:{outcome}")
    box = dynamic_mesh.get_mesh_bounding_box()
    minimum = vector(box.min)
    maximum = vector(box.max)
    return {
        "minimum_cm": minimum,
        "maximum_cm": maximum,
        "dimensions_cm": [maximum[index] - minimum[index] for index in range(3)],
        "pivot_cm": [0.0, 0.0, 0.0],
    }


def assert_bounds(actual: dict, expected: dict, tolerance: float, label: str) -> None:
    for field in ("minimum_cm", "maximum_cm", "dimensions_cm"):
        delta = [float(actual[field][index]) - float(expected[field][index]) for index in range(3)]
        if max(abs(value) for value in delta) > tolerance:
            fail(label + " " + field + " drift: " + repr(delta))


def global_slot_names(mesh: unreal.StaticMesh) -> list[str]:
    return [
        str(row.get_editor_property("material_slot_name"))
        for row in mesh.get_editor_property("static_materials")
    ]


def section_slot_names(mesh: unreal.StaticMesh, subsystem, lod_index: int, slots: list[str]) -> list[str]:
    output = []
    for section_index in range(int(mesh.get_num_sections(lod_index))):
        slot_index = int(subsystem.get_lod_material_slot(mesh, lod_index, section_index))
        if slot_index < 0 or slot_index >= len(slots):
            fail(f"section material index invalid: {mesh.get_name()}:LOD{lod_index}:{section_index}")
        output.append(slots[slot_index])
    return output


def import_data_contract(mesh: unreal.StaticMesh) -> dict:
    data = mesh.get_editor_property("asset_import_data")
    output = {
        "import_uniform_scale": float(data.get_editor_property("import_uniform_scale")),
        "convert_scene": bool(data.get_editor_property("convert_scene")),
        "convert_scene_unit": bool(data.get_editor_property("convert_scene_unit")),
        "force_front_x_axis": bool(data.get_editor_property("force_front_x_axis")),
        "transform_vertex_to_absolute": bool(data.get_editor_property("transform_vertex_to_absolute")),
        "bake_pivot_in_vertex": bool(data.get_editor_property("bake_pivot_in_vertex")),
        "generate_lightmap_u_vs": bool(data.get_editor_property("generate_lightmap_u_vs")),
        "auto_generate_collision": bool(data.get_editor_property("auto_generate_collision")),
        "remove_degenerates": bool(data.get_editor_property("remove_degenerates")),
    }
    expected = {
        "import_uniform_scale": 1.0,
        "convert_scene": True,
        "convert_scene_unit": True,
        "force_front_x_axis": False,
        "transform_vertex_to_absolute": True,
        "bake_pivot_in_vertex": False,
        "generate_lightmap_u_vs": False,
        "auto_generate_collision": False,
        "remove_degenerates": False,
    }
    if output != expected:
        fail("legacy FBX import setting drift: " + mesh.get_name() + ":" + repr(output))
    return output


def make_import_task(spec: dict):
    lod0 = spec["lods"][0]
    source = PROJECT / lod0["source"]
    if not source.is_file() or sha256(source) != str(lod0["source_sha256"]).upper():
        fail("LOD0 source hash drift before import: " + str(source))
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(source),
        "destination_path": DEST + "/" + spec["category"],
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
        "create_physics_asset": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
        "original_import_type": unreal.FBXImportType.FBXIT_STATIC_MESH,
        "automated_import_should_detect_type": False,
        "override_full_name": True,
        "auto_compute_lod_distances": False,
        "lod_number": 1,
        "minimum_lod_number": 0,
    })
    data = options.get_editor_property("static_mesh_import_data")
    data.set_editor_properties({
        "import_uniform_scale": 1.0,
        "combine_meshes": True,
        "import_mesh_lods": False,
        "convert_scene": True,
        "convert_scene_unit": True,
        "force_front_x_axis": False,
        "transform_vertex_to_absolute": True,
        "bake_pivot_in_vertex": False,
        "generate_lightmap_u_vs": False,
        "auto_generate_collision": False,
        "remove_degenerates": False,
        "build_nanite": False,
        "reorder_material_to_fbx_order": True,
    })
    task.set_editor_property("options", options)
    return task


def append_all_custom_lods_legacy(meshes: dict, baseline: dict, subsystem) -> dict:
    previous = int(unreal.SystemLibrary.get_console_variable_int_value(INTERCHANGE_FBX_CVAR))
    evidence = {
        "name": INTERCHANGE_FBX_CVAR,
        "previous_value": previous,
        "disabled_value": None,
        "restored_value": None,
        "set_false_only_around_custom_lod_imports": True,
        "custom_lods_requested": 24,
        "custom_lods_imported": [],
        "restore_attempted_in_finally": False,
    }
    if previous not in (0, 1):
        fail("unexpected Interchange FBX feature flag value: " + str(previous))
    import_error = None
    try:
        unreal.SystemLibrary.execute_console_command(None, INTERCHANGE_FBX_CVAR + " 0")
        evidence["disabled_value"] = int(
            unreal.SystemLibrary.get_console_variable_int_value(INTERCHANGE_FBX_CVAR)
        )
        if evidence["disabled_value"] != 0:
            fail("could not disable Interchange FBX translator for legacy custom LOD import")
        for key, spec in sorted(baseline["assets"].items()):
            mesh = meshes[key]
            for lod in spec["lods"][1:]:
                lod_index = int(lod["lod"])
                if int(mesh.get_num_lods()) != lod_index:
                    fail(f"fresh append-only LOD precondition failed: {key}:LOD{lod_index}")
                source = PROJECT / lod["source"]
                if not source.is_file() or sha256(source) != str(lod["source_sha256"]).upper():
                    fail(f"custom LOD source hash drift: {key}:LOD{lod_index}")
                result = subsystem.import_lod(mesh, lod_index, str(source))
                if int(result) != lod_index:
                    fail(f"legacy custom LOD import failed: {key}:LOD{lod_index}:returned={result}")
                unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
                evidence["custom_lods_imported"].append({
                    "asset_key": key,
                    "lod": lod_index,
                    "source": lod["source"],
                    "source_sha256": lod["source_sha256"],
                })
    except Exception as error:
        import_error = error
    finally:
        evidence["restore_attempted_in_finally"] = True
        unreal.SystemLibrary.execute_console_command(None, f"{INTERCHANGE_FBX_CVAR} {previous}")
        evidence["restored_value"] = int(
            unreal.SystemLibrary.get_console_variable_int_value(INTERCHANGE_FBX_CVAR)
        )
    if evidence["restored_value"] != previous:
        fail("Interchange FBX feature flag restoration drift: " + repr(evidence))
    if import_error is not None:
        raise import_error
    if len(evidence["custom_lods_imported"]) != 24:
        fail("legacy custom LOD import count drift")
    evidence["status"] = (
        "PASS__INTERCHANGE_FBX_DISABLED_ONLY_FOR_24_LEGACY_CUSTOM_LOD_IMPORTS__RESTORED"
    )
    return evidence


def prepare_mesh_before_screen_phase(
        key: str, spec: dict, subsystem, materials: dict, mesh: unreal.StaticMesh) -> None:
    if not isinstance(mesh, unreal.StaticMesh) or mesh.get_path_name() != spec["object_path"]:
        fail("imported StaticMesh/object path drift: " + key)
    if int(mesh.get_num_lods()) != 3:
        fail("fresh custom-LOD append did not produce exactly three source models: " + key)

    nanite = subsystem.get_nanite_settings(mesh)
    nanite.set_editor_property("enabled", False)
    subsystem.set_nanite_settings(mesh, nanite, True)
    body = mesh.get_editor_property("body_setup")
    if body is None:
        fail("BodySetup missing: " + key)
    if (int(unreal.EditorStaticMeshLibrary.get_simple_collision_count(mesh)) != 0
            or int(unreal.EditorStaticMeshLibrary.get_convex_collision_count(mesh)) != 0):
        fail("fresh import unexpectedly contains collision before deterministic box creation: " + key)
    unreal.EditorStaticMeshLibrary.add_simple_collisions(mesh, unreal.ScriptingCollisionShapeType.BOX)
    body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_DEFAULT)

    expected_global_slots = list(spec["lods"][0]["material_slots"])
    slots = global_slot_names(mesh)
    if slots != expected_global_slots:
        fail("LOD0/global semantic material-slot order drift: " + key + ":" + repr(slots))
    for index, slot_name in enumerate(slots):
        material = materials.get(slot_name)
        if material is None:
            fail("unbound semantic material slot: " + key + ":" + slot_name)
        mesh.set_material(index, material)

    if not library.save_loaded_asset(mesh, only_if_is_dirty=False):
        fail("pre-screen StaticMesh save failed: " + key)


def persist_all_manual_screen_sizes(meshes: dict, baseline: dict, subsystem) -> dict:
    # All LOD, Nanite, collision and material edits across all twelve meshes are
    # complete before pass one. Pass two is the final edit/save phase globally;
    # no compilation, build or PostEditChange operation is allowed afterwards.
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    screen_sizes = [float(value) for value in baseline["import_contract"]["lod_screen_sizes"]]
    expected_screens = [round(value, 6) for value in screen_sizes]
    if int(baseline["import_contract"]["screen_size_persistence_passes"]) != 2:
        fail("screen-size persistence pass-count contract drift")
    output = {key: {"passes": []} for key in meshes}
    for key, mesh in sorted(meshes.items()):
        if not subsystem.set_lod_screen_sizes(mesh, screen_sizes):
            fail("first manual LOD screen-size assignment failed: " + key)
        immediate = [round(float(value), 6) for value in subsystem.get_lod_screen_sizes(mesh)]
        auto = bool(mesh.is_lod_screen_size_auto_computed())
        if immediate != expected_screens or auto:
            fail("first LOD screen-size write/readback drift: " + key + ":" + repr(immediate))
        if not library.save_loaded_asset(mesh, only_if_is_dirty=False):
            fail("first screen-size persistence save failed: " + key)
        output[key]["passes"].append({
            "pass": 1,
            "immediate_readback": immediate,
            "immediate_auto_compute": auto,
        })

    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    for key, mesh in sorted(meshes.items()):
        readback = [round(float(value), 6) for value in subsystem.get_lod_screen_sizes(mesh)]
        auto = bool(mesh.is_lod_screen_size_auto_computed())
        output[key]["passes"][0].update({
            "post_save_compile_readback_before_reapply": readback,
            "post_save_compile_auto_compute_before_reapply": auto,
        })
    for key, mesh in sorted(meshes.items()):
        if not subsystem.set_lod_screen_sizes(mesh, screen_sizes):
            fail("final manual LOD screen-size assignment failed: " + key)
        immediate = [round(float(value), 6) for value in subsystem.get_lod_screen_sizes(mesh)]
        auto = bool(mesh.is_lod_screen_size_auto_computed())
        if immediate != expected_screens or auto:
            fail("final pre-save LOD screen-size drift: " + key + ":" + repr(immediate))
        if not library.save_loaded_asset(mesh, only_if_is_dirty=False):
            fail("final screen-size persistence save failed: " + key)
        final = [round(float(value), 6) for value in subsystem.get_lod_screen_sizes(mesh)]
        final_auto = bool(mesh.is_lod_screen_size_auto_computed())
        if final != expected_screens or final_auto:
            fail("final LOD screen-size persistence drift: " + key + ":" + repr(final))
        output[key]["passes"].append({
            "pass": 2,
            "immediate_readback": immediate,
            "immediate_auto_compute": auto,
            "post_final_save_readback": final,
            "post_final_save_auto_compute": final_auto,
        })
        output[key].update({
            "write_order": baseline["import_contract"]["screen_size_write_order"],
            "global_final_phase_after_all_mesh_preparation": True,
            "no_build_after_final_set": True,
            "fresh_process_readback_required": True,
        })
    return output


def measure_final_mesh(
        key: str, spec: dict, baseline: dict, subsystem, mesh: unreal.StaticMesh,
        screen_evidence: dict) -> dict:
    if not isinstance(mesh, unreal.StaticMesh) or mesh.get_path_name() != spec["object_path"]:
        fail("final StaticMesh/object path drift: " + key)
    if int(mesh.get_num_lods()) != 3:
        fail("LOD count drift: " + key)
    final_screens = [round(float(value), 6) for value in subsystem.get_lod_screen_sizes(mesh)]
    final_auto = bool(mesh.is_lod_screen_size_auto_computed())
    expected_screens = [
        round(float(value), 6) for value in baseline["import_contract"]["lod_screen_sizes"]
    ]
    if final_screens != expected_screens or final_auto:
        fail("global final LOD screen-size phase drift: " + key + ":" + repr(final_screens))
    if (screen_evidence.get("global_final_phase_after_all_mesh_preparation") is not True
            or screen_evidence.get("no_build_after_final_set") is not True
            or len(screen_evidence.get("passes", [])) != 2):
        fail("global final screen-write evidence drift: " + key)

    slots = global_slot_names(mesh)
    expected_global_slots = list(spec["lods"][0]["material_slots"])
    if slots != expected_global_slots:
        fail("final global semantic material-slot order drift: " + key)
    tolerance = float(baseline["import_contract"]["bounds_tolerance_cm"])
    lod_rows = []
    for lod_index, expected_lod in enumerate(spec["lods"]):
        triangles = int(mesh.get_num_triangles(lod_index))
        if triangles != int(expected_lod["triangles"]):
            fail(f"triangle contract drift: {key}:LOD{lod_index}:{triangles}")
        bounds = lod_bounds(mesh, lod_index)
        assert_bounds(bounds, expected_lod["expected_unreal_bounds"], tolerance, f"{key}:LOD{lod_index}")
        if (abs(bounds["minimum_cm"][2]) > float(baseline["import_contract"]["pivot_tolerance_cm"])
                or abs((bounds["minimum_cm"][0] + bounds["maximum_cm"][0]) * 0.5) > tolerance
                or abs((bounds["minimum_cm"][1] + bounds["maximum_cm"][1]) * 0.5) > tolerance):
            fail(f"floor-centred pivot contract drift: {key}:LOD{lod_index}")
        sections = section_slot_names(mesh, subsystem, lod_index, slots)
        if sections != list(expected_lod["material_slots"]):
            fail(f"per-LOD section/material order drift: {key}:LOD{lod_index}:{sections}")
        uv_channels = int(mesh.get_num_tex_coords(lod_index))
        if uv_channels != int(baseline["import_contract"]["expected_uv_channels_per_lod"]):
            fail(f"UV channel contract drift: {key}:LOD{lod_index}:{uv_channels}")
        lod_rows.append({
            "lod": lod_index,
            "triangles": triangles,
            "vertices": int(mesh.get_num_vertices(lod_index)),
            "uv_channels": uv_channels,
            "bounds": bounds,
            "section_material_slots": sections,
            "source": expected_lod["source"],
            "source_sha256": expected_lod["source_sha256"],
        })
    triangle_chain = [row["triangles"] for row in lod_rows]
    if not (triangle_chain[0] > triangle_chain[1] > triangle_chain[2] > 0):
        fail("imported strict monotonic triangle contract drift: " + key + ":" + repr(triangle_chain))

    body = mesh.get_editor_property("body_setup")
    if body is None:
        fail("final BodySetup missing: " + key)
    simple = int(unreal.EditorStaticMeshLibrary.get_simple_collision_count(mesh))
    convex = int(unreal.EditorStaticMeshLibrary.get_convex_collision_count(mesh))
    trace = str(body.get_editor_property("collision_trace_flag"))
    nanite_enabled = bool(subsystem.get_nanite_settings(mesh).get_editor_property("enabled"))
    collision = spec["collision"]
    if (simple != int(collision["simple_count"])
            or convex != int(collision["convex_count"])
            or "USE_DEFAULT" not in trace.upper()
            or nanite_enabled):
        fail("collision/Nanite contract drift: " + key + f":{simple}:{convex}:{trace}:{nanite_enabled}")
    bound_materials = [
        mesh.get_material(index).get_path_name() if mesh.get_material(index) else None
        for index in range(len(slots))
    ]
    expected_materials = [
        object_path(baseline["import_contract"]["material_bindings"][slot]) for slot in slots
    ]
    if bound_materials != expected_materials:
        fail("deterministic presentation-material binding drift: " + key)
    package = package_file(spec["package_path"])
    if not package.is_file():
        fail("saved package missing: " + str(package))
    package_row = file_row(package)
    return {
        "asset_key": key,
        "semantic_role": spec["semantic_role"],
        "wip_contract": spec["wip_contract"],
        "package_path": spec["package_path"],
        "object_path": mesh.get_path_name(),
        "package": package_row,
        "lod_count": 3,
        "lod_screen_sizes": final_screens,
        "lod_screen_size_auto_computed": final_auto,
        "screen_size_persistence": {
            **screen_evidence,
        },
        "lods": lod_rows,
        "triangle_chain": triangle_chain,
        "strict_monotonic_triangles": True,
        "global_material_slots": slots,
        "bound_materials": bound_materials,
        "simple_collision_count": simple,
        "convex_collision_count": convex,
        "collision_trace_flag": trace,
        "nanite_enabled": nanite_enabled,
        "legacy_import_data": import_data_contract(mesh),
    }


def main() -> None:
    run_root = resolve_run_root()
    receipt = run_root / IMPORT_RECEIPT_NAME
    failure_receipt = run_root / IMPORT_FAILURE_NAME
    evidence = {
        "$schema": "lineboss/audit/bodyshop-support-kit-native-v001-unreal-import/v2",
        "generated_utc": now(),
        "process_id": os.getpid(),
        "destination_namespace": DEST,
        "writes_authorized": [str(DEST_DISK), str(run_root)],
        "maps_loaded_or_saved": [],
        "source_config_save_changes": [],
        "runtime_binding_or_promotion_changes": [],
    }
    source_before = None
    protected_before = None
    try:
        if receipt.exists() or failure_receipt.exists():
            fail("run directory already contains an import result")
        baseline = load_baseline()
        evidence["baseline_sha256"] = sha256(BASELINE)
        evidence["baseline_status"] = baseline["status"]
        existing_results = prior_result_files(run_root)
        if existing_results:
            fail("v002 refuses every pre-existing lane result: " + repr(existing_results))
        if DEST_DISK.exists() or library.does_directory_exist(DEST):
            fail("isolated destination already exists; overwrite/retry is forbidden")
        if namespace_disk_inventory():
            fail("isolated destination disk inventory is not empty")
        if library.list_assets(DEST, recursive=True, include_folder=False):
            fail("asset registry already exposes the isolated destination")
        for spec in baseline["assets"].values():
            if library.does_asset_exist(spec["package_path"]):
                fail("fresh object path already exists: " + spec["package_path"])

        source_before = verify_source(baseline)
        protected_before = verify_protected_metadata_and_critical_hashes(baseline)
        evidence["source_before"] = source_before
        evidence["protected_before"] = protected_before

        materials = {}
        for slot, package_path in baseline["import_contract"]["material_bindings"].items():
            material = library.load_asset(package_path)
            if not isinstance(material, unreal.MaterialInterface):
                fail("protected presentation material missing/wrong type: " + package_path)
            materials[slot] = material

        tasks = []
        task_keys = []
        for key, spec in sorted(baseline["assets"].items()):
            tasks.append(make_import_task(spec))
            task_keys.append(key)
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        for key, task in zip(task_keys, tasks):
            imported = [str(value) for value in task.get_editor_property("imported_object_paths")]
            expected = baseline["assets"][key]["object_path"]
            if imported != [expected]:
                fail("LOD0 task result drift: " + key + ":" + repr(imported))

        subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        if subsystem is None:
            fail("StaticMeshEditorSubsystem unavailable; use full UnrealEditor -ExecutePythonScript")
        loaded_meshes = {}
        for key, spec in sorted(baseline["assets"].items()):
            mesh = library.load_asset(spec["package_path"])
            if not isinstance(mesh, unreal.StaticMesh) or mesh.get_path_name() != spec["object_path"]:
                fail("fresh LOD0 StaticMesh/object path drift: " + key)
            if int(mesh.get_num_lods()) != 1:
                fail("fresh LOD0 import did not produce exactly one source model: " + key)
            loaded_meshes[key] = mesh
        cvar_evidence = append_all_custom_lods_legacy(loaded_meshes, baseline, subsystem)
        evidence["interchange_fbx_legacy_custom_lod_guard"] = cvar_evidence
        for key, spec in sorted(baseline["assets"].items()):
            prepare_mesh_before_screen_phase(
                key, spec, subsystem, materials, loaded_meshes[key],
            )
        screen_phase = persist_all_manual_screen_sizes(loaded_meshes, baseline, subsystem)
        evidence["global_final_screen_size_phase"] = screen_phase
        meshes = {}
        for key, spec in sorted(baseline["assets"].items()):
            meshes[key] = measure_final_mesh(
                key, spec, baseline, subsystem, loaded_meshes[key], screen_phase[key],
            )

        expected_registry = {spec["package_path"] for spec in baseline["assets"].values()}
        registry = {
            str(path).rsplit(".", 1)[0]
            for path in library.list_assets(DEST, recursive=True, include_folder=False)
        }
        if registry != expected_registry:
            fail("exact twelve-package asset-registry inventory drift: " + repr(sorted(registry)))
        disk = namespace_disk_inventory()
        expected_disk = {spec["disk_path"] for spec in baseline["assets"].values()}
        if set(disk) != expected_disk:
            fail("exact twelve-package disk inventory drift: " + repr(sorted(disk)))

        source_after = verify_source(baseline)
        protected_after = verify_protected_metadata_and_critical_hashes(baseline)
        if source_after != source_before:
            fail("frozen source changed during import")
        if protected_after != protected_before:
            fail("Source/Config/saves/maps/materials or existing Content changed during import")
        if int(unreal.SystemLibrary.get_console_variable_int_value(INTERCHANGE_FBX_CVAR)) != int(
                cvar_evidence["previous_value"]):
            fail("Interchange FBX feature flag changed after restoration")

        evidence.update({
            "status": "PASS__HASH_GUARDED_FROZEN_BODYSHOP_SUPPORT_KIT_NATIVE_V001_BASELINE_V002_UNREAL_INTAKE",
            "engine_version": str(unreal.SystemLibrary.get_engine_version()),
            "source_after": source_after,
            "protected_after": protected_after,
            "assets": meshes,
            "asset_registry_packages": sorted(registry),
            "namespace_disk_files": disk,
            "asset_count": len(meshes),
            "lod_count_per_asset": 3,
            "source_fbx_count": 36,
            "new_material_or_texture_assets": 0,
            "material_policy": baseline["import_contract"]["material_policy"],
            "collision_policy": baseline["import_contract"]["collision"],
            "fresh_process_validator_required": True,
            "strict_per_asset_monotonic_triangles_verified": True,
            "exact_one_uv_channel_per_lod_verified": True,
            "automatic_cleanup": "NOT_PERFORMED__PARTIAL_ARTIFACTS_PRESERVED_FOR_EXPLICIT_REVIEW",
            "failures": [],
        })
        receipt.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        unreal.log("LINE_BOSS_BODYSHOP_SUPPORT_KIT_NATIVE_V001_LANE_V002_HASH_GUARDED_IMPORT_PASS")
        print(json.dumps(evidence, indent=2))
        unreal.SystemLibrary.quit_editor()
    except Exception as error:
        record = dict(evidence)
        record.update({
            "status": "FAIL_CLOSED__BODYSHOP_SUPPORT_KIT_NATIVE_V001_UNREAL_IMPORT_LANE_V002",
            "error": str(error),
            "traceback": traceback.format_exc(),
            "source_before": source_before,
            "protected_before": protected_before,
            "namespace_files_preserved_for_recovery": namespace_disk_inventory(),
            "automatic_cleanup": "NOT_PERFORMED__PARTIAL_ARTIFACTS_PRESERVED_FOR_EXPLICIT_REVIEW",
            "recovery": "Archive this run; do not rerun lane v002 or delete/replace a package implicitly.",
        })
        failure_receipt.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        unreal.log_error("LINE_BOSS_BODYSHOP_SUPPORT_KIT_NATIVE_V001_LANE_V002_IMPORT_FAIL: " + str(error))
        print(json.dumps(record, indent=2))
        try:
            unreal.SystemLibrary.quit_editor()
        finally:
            raise


if __name__ == "__main__":
    main()
