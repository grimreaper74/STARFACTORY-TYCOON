"""Fail-closed UE-native scratch intake for MaterialFlow RuntimePrep v002.

This deliberately imports only into a fresh scratch namespace.  Its purpose
is to prove that Unreal 5.8's *native legacy* FbxFactory obeys v002's new
raw-control-point scale/pivot contract before any promotion lane creates
production assets or changes the press presentation.
"""

from __future__ import annotations

import hashlib
import json
import traceback
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
EXPECTED_PROJECT = Path(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8").resolve()
SOURCE = PROJECT / "ArtSource/Claude_PressShop_MaterialFlowPack_RuntimePrep_v002"
STATS = SOURCE / "runtime_prep_stats_v002.json"
DESTINATION = (
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/_Scratch/"
    "MaterialFlowPack_v002_LegacyFbxFactory_v001"
)
DESTINATION_DISK = PROJECT / "Content" / Path(DESTINATION.removeprefix("/Game/"))
AUDIT_DIR = PROJECT / "Saved/Audits/OneFactory/Press/MaterialFlowPackRuntimePrep_v002"
RECEIPT = AUDIT_DIR / "legacy_fbx_factory_scratch_v001.json"
FAILURE = AUDIT_DIR / "legacy_fbx_factory_scratch_v001_failure.json"
INTERCHANGE_FBX_CVAR = "Interchange.FeatureFlags.Import.FBX"
TOLERANCE_CM = 0.25

LIBRARY = unreal.EditorAssetLibrary
ASSET_TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
MESH_EDITOR = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def fail(message: str) -> None:
    raise RuntimeError("MATERIAL_FLOW_V002_LEGACY_FBX_FACTORY_SCRATCH_FAIL: " + message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_json(value) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def write_once(path: Path, payload: dict) -> None:
    if path.exists():
        fail("refusing to overwrite existing evidence: " + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(payload), encoding="utf-8")


def content_fingerprint(excluded_root: Path) -> dict[str, tuple[int, int]]:
    """A lightweight guard that no existing content package was altered."""
    content = PROJECT / "Content"
    rows = {}
    for path in content.rglob("*"):
        if not path.is_file():
            continue
        try:
            path.resolve().relative_to(excluded_root.resolve())
            continue
        except ValueError:
            pass
        stat = path.stat()
        rows[str(path.relative_to(content)).replace("\\", "/")] = (
            int(stat.st_size), int(stat.st_mtime_ns)
        )
    return rows


def source_contract() -> dict:
    if PROJECT != EXPECTED_PROJECT:
        fail("wrong project: " + str(PROJECT))
    if str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory":
        fail("wrong game name")
    if not SOURCE.is_dir() or not STATS.is_file():
        fail("v002 source/stats missing")
    stats = json.loads(STATS.read_text(encoding="utf-8"))
    if stats.get("asset_pack") != "CA_PressShop_MaterialFlowPack_RuntimePrep_v002":
        fail("source pack identity drift")
    contract = stats.get("ue_native_import_contract", {})
    expected_contract = {
        "importer": "Unreal 5.8 native legacy FbxFactory",
        "Combine Meshes": False,
        "Convert Scene": True,
        "Convert Scene Unit": True,
        "transform_vertex_to_absolute": False,
        "bake_pivot_in_vertex": False,
    }
    if {key: contract.get(key) for key in expected_contract} != expected_contract:
        fail("v002 UE native import contract drift: " + repr(contract))
    if stats.get("totals", {}).get("modules") != 6:
        fail("v002 module total is not six")
    if stats.get("totals", {}).get("meshes") != 10:
        fail("v002 mesh total is not ten")
    if stats.get("totals", {}).get("payload_triangles") != 3792:
        fail("v002 triangle total is not 3792")
    modules = stats.get("modules", {})
    if len(modules) != 6:
        fail("v002 module table drift")
    seen_meshes = set()
    source_hashes = {"stats_sha256": sha256(STATS), "fbx": {}}
    expected_module_counts = {}
    for module_name, module in sorted(modules.items()):
        filename = module.get("file")
        fbx = SOURCE / str(filename)
        if not filename or not fbx.is_file():
            fail("missing v002 FBX for " + module_name)
        actual_hash = sha256(fbx)
        if actual_hash != module.get("fbx_sha256"):
            fail("FBX hash drift for " + module_name)
        source_hashes["fbx"][str(filename)] = actual_hash
        meshes = module.get("meshes", {})
        if not meshes:
            fail("module has no semantic meshes: " + module_name)
        expected_module_counts[module_name] = len(meshes)
        for semantic_name, spec in meshes.items():
            if semantic_name in seen_meshes:
                fail("duplicate semantic mesh " + semantic_name)
            seen_meshes.add(semantic_name)
            if int(spec.get("triangles", -1)) <= 0:
                fail("invalid triangle count: " + semantic_name)
            bounds = spec.get("expected_ue_aabb_cm", {})
            if len(bounds.get("min", ())) != 3 or len(bounds.get("max", ())) != 3:
                fail("missing expected UE bounds: " + semantic_name)
            if tuple(spec.get("uv_layers", ())) != ("UVMap", "UV_Unique"):
                fail("UV channel source contract drift: " + semantic_name)
            if not spec.get("material_slots"):
                fail("material-slot source contract missing: " + semantic_name)
    if len(seen_meshes) != 10:
        fail("semantic mesh inventory is not ten")
    return {
        "stats": stats,
        "source_hashes": source_hashes,
        "expected_module_counts": expected_module_counts,
        "semantic_meshes": seen_meshes,
    }


def normalise_terminal_blender_slot_suffix(name: str) -> str:
    """Only remove Blender's final .ddd duplicate suffix, if present."""
    if len(name) >= 4 and name[-4] == "." and name[-3:].isdigit():
        return name[:-4]
    return name


def vector(value) -> list[float]:
    return [round(float(value.x), 5), round(float(value.y), 5), round(float(value.z), 5)]


def lod0_bounds(mesh) -> dict:
    dynamic_mesh = unreal.DynamicMesh()
    options = unreal.GeometryScriptCopyMeshFromAssetOptions()
    requested_lod = unreal.GeometryScriptMeshReadLOD()
    requested_lod.set_editor_properties({
        "lod_type": unreal.GeometryScriptLODType.SOURCE_MODEL,
        "lod_index": 0,
    })
    dynamic_mesh, outcome = unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(
        mesh, dynamic_mesh, options, requested_lod, False
    )
    if outcome != unreal.GeometryScriptOutcomePins.SUCCESS:
        fail("source LOD bounds extraction failed for {}: {}".format(mesh.get_name(), outcome))
    box = dynamic_mesh.get_mesh_bounding_box()
    minimum, maximum = vector(box.min), vector(box.max)
    return {
        "min": minimum,
        "max": maximum,
        "dimensions": [round(maximum[index] - minimum[index], 5) for index in range(3)],
    }


def within_tolerance(actual: list[float], expected: list[float], tolerance: float = TOLERANCE_CM) -> bool:
    return len(actual) == len(expected) and all(
        abs(float(actual[index]) - float(expected[index])) <= tolerance
        for index in range(len(expected))
    )


def raw_slot_names(mesh) -> tuple[list[str], list[str]]:
    raw = [str(slot.get_editor_property("material_slot_name"))
           for slot in mesh.get_editor_property("static_materials")]
    return raw, [normalise_terminal_blender_slot_suffix(name) for name in raw]


def make_import_task(fbx: Path) -> unreal.AssetImportTask:
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(fbx),
        "destination_path": DESTINATION,
        "automated": True,
        "async_": False,
        "replace_existing": False,
        "replace_existing_settings": False,
        "save": True,
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
    })
    data = options.get_editor_property("static_mesh_import_data")
    data.set_editor_properties({
        "combine_meshes": False,
        "import_mesh_lods": False,
        "import_uniform_scale": 1.0,
        "convert_scene": True,
        "convert_scene_unit": True,
        "force_front_x_axis": False,
        "transform_vertex_to_absolute": False,
        "bake_pivot_in_vertex": False,
        "generate_lightmap_u_vs": False,
        "auto_generate_collision": False,
        "remove_degenerates": False,
        "build_nanite": False,
        "reorder_material_to_fbx_order": True,
    })
    # Explicit legacy factory plus the transient feature flag below prevents
    # UE 5.8 from silently routing this FBX through Interchange.
    factory = unreal.FbxFactory()
    factory.set_editor_property("asset_import_task", task)
    task.set_editor_property("factory", factory)
    task.set_editor_property("options", options)
    return task


def legacy_import_data(mesh) -> dict:
    data = mesh.get_editor_property("asset_import_data")
    try:
        values = {
            "class": str(data.get_class().get_name()),
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
    except Exception as error:
        fail("legacy FBX import data unavailable (Interchange is not accepted): {}: {}".format(
            mesh.get_name(), error
        ))
    expected = {
        "import_uniform_scale": 1.0,
        "convert_scene": True,
        "convert_scene_unit": True,
        "force_front_x_axis": False,
        "transform_vertex_to_absolute": False,
        "bake_pivot_in_vertex": False,
        "generate_lightmap_u_vs": False,
        "auto_generate_collision": False,
        "remove_degenerates": False,
    }
    actual = {key: values[key] for key in expected}
    if actual != expected:
        fail("legacy FBX import setting drift for {}: {}".format(mesh.get_name(), actual))
    if "Fbx" not in values["class"]:
        fail("asset import data is not legacy FbxStaticMeshImportData: {}".format(values["class"]))
    return values


def mesh_observation(mesh) -> dict:
    if not isinstance(mesh, unreal.StaticMesh):
        fail("imported non-StaticMesh: " + str(mesh))
    raw_slots, slots = raw_slot_names(mesh)
    bounds = lod0_bounds(mesh)
    simple_collision = int(MESH_EDITOR.get_simple_collision_count(mesh))
    convex_collision = int(MESH_EDITOR.get_convex_collision_count(mesh))
    if simple_collision or convex_collision:
        fail("unexpected collision on {}: {}".format(
            mesh.get_name(), [simple_collision, convex_collision]
        ))
    nanite = MESH_EDITOR.get_nanite_settings(mesh)
    if bool(nanite.get_editor_property("enabled")):
        fail("unexpected Nanite enablement on " + mesh.get_name())
    if int(mesh.get_num_lods()) != 1:
        fail("unexpected LOD count on {}: {}".format(mesh.get_name(), mesh.get_num_lods()))
    uv_channels = int(MESH_EDITOR.get_num_uv_channels(mesh, 0))
    if uv_channels != 2:
        fail("UV-channel contract drift on {}: {}".format(mesh.get_name(), uv_channels))
    return {
        "object_path": str(mesh.get_path_name()),
        "raw_asset_name": str(mesh.get_name()),
        "triangles": int(mesh.get_num_triangles(0)),
        "lods": int(mesh.get_num_lods()),
        "uv_channels": uv_channels,
        "source_lod0_bounds_cm": bounds,
        "render_bounds_cm": {
            "min": vector(mesh.get_bounding_box().min),
            "max": vector(mesh.get_bounding_box().max),
        },
        "raw_slot_names": raw_slots,
        "normalised_slot_names": slots,
        "simple_collision_count": simple_collision,
        "convex_collision_count": convex_collision,
        "nanite_enabled": False,
        "legacy_import_data": legacy_import_data(mesh),
    }


def semantic_match(observation: dict, specs: dict, already_matched: set[str]) -> str:
    candidates = []
    for semantic_name, spec in specs.items():
        if semantic_name in already_matched:
            continue
        expected_bounds = spec["expected_ue_aabb_cm"]
        if int(spec["triangles"]) != observation["triangles"]:
            continue
        if list(spec["material_slots"]) != observation["normalised_slot_names"]:
            continue
        bounds = observation["source_lod0_bounds_cm"]
        if not within_tolerance(bounds["min"], list(expected_bounds["min"])):
            continue
        if not within_tolerance(bounds["max"], list(expected_bounds["max"])):
            continue
        candidates.append(semantic_name)
    if len(candidates) != 1:
        fail("could not map imported {} to one semantic mesh; candidates={}".format(
            observation["object_path"], candidates
        ))
    return candidates[0]


def import_all_modules(contract: dict) -> tuple[dict, dict]:
    stats = contract["stats"]
    modules = stats["modules"]
    previous = int(unreal.SystemLibrary.get_console_variable_int_value(INTERCHANGE_FBX_CVAR))
    if previous not in (0, 1):
        fail("unexpected Interchange FBX feature flag value: " + str(previous))
    cvar_evidence = {
        "name": INTERCHANGE_FBX_CVAR,
        "previous_value": previous,
        "disabled_value": None,
        "restored_value": None,
        "restore_attempted_in_finally": False,
        "explicit_factory": "FbxFactory",
    }
    imported = {}
    import_error = None
    try:
        unreal.SystemLibrary.execute_console_command(None, INTERCHANGE_FBX_CVAR + " 0")
        cvar_evidence["disabled_value"] = int(
            unreal.SystemLibrary.get_console_variable_int_value(INTERCHANGE_FBX_CVAR)
        )
        if cvar_evidence["disabled_value"] != 0:
            fail("could not disable Interchange FBX translator")
        for module_name, module in sorted(modules.items()):
            task = make_import_task(SOURCE / module["file"])
            ASSET_TOOLS.import_asset_tasks([task])
            unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
            paths = [str(path) for path in (task.get_editor_property("imported_object_paths") or [])]
            expected_count = contract["expected_module_counts"][module_name]
            if len(paths) != expected_count:
                fail("{} yielded {} objects, expected {}: {}".format(
                    module_name, len(paths), expected_count, paths
                ))
            rows = []
            for path in paths:
                mesh = unreal.load_asset(path)
                if mesh is None:
                    fail("could not load imported object " + path)
                rows.append(mesh_observation(mesh))
            imported[module_name] = rows
    except Exception as error:
        import_error = error
    finally:
        cvar_evidence["restore_attempted_in_finally"] = True
        unreal.SystemLibrary.execute_console_command(None, "{} {}".format(INTERCHANGE_FBX_CVAR, previous))
        cvar_evidence["restored_value"] = int(
            unreal.SystemLibrary.get_console_variable_int_value(INTERCHANGE_FBX_CVAR)
        )
    if cvar_evidence["restored_value"] != previous:
        fail("Interchange FBX feature flag restoration drift: " + repr(cvar_evidence))
    if import_error is not None:
        raise import_error
    return imported, cvar_evidence


def validate_imported(imported: dict, contract: dict) -> dict:
    specs = {}
    for module in contract["stats"]["modules"].values():
        specs.update(module["meshes"])
    matched = set()
    results = {}
    observed_total = 0
    for module_name, rows in sorted(imported.items()):
        module_results = []
        for row in rows:
            semantic_name = semantic_match(row, specs, matched)
            matched.add(semantic_name)
            expected = specs[semantic_name]
            observed_total += row["triangles"]
            module_results.append({
                "semantic_mesh": semantic_name,
                "expected_ue_aabb_cm": expected["expected_ue_aabb_cm"],
                "expected_triangles": int(expected["triangles"]),
                "mover": expected.get("mover"),
                **row,
            })
        results[module_name] = module_results
    if matched != contract["semantic_meshes"]:
        fail("semantic imported inventory drift: missing={} extra={}".format(
            sorted(contract["semantic_meshes"] - matched), sorted(matched - contract["semantic_meshes"])
        ))
    if observed_total != 3792:
        fail("native payload triangles {} rather than 3792".format(observed_total))
    return {"modules": results, "native_meshes": len(matched), "native_triangles": observed_total}


def main() -> dict:
    if DESTINATION_DISK.exists() or LIBRARY.does_directory_exist(DESTINATION):
        fail("scratch destination already exists: " + DESTINATION)
    if RECEIPT.exists() or FAILURE.exists():
        fail("scratch evidence already exists; use a new revision rather than overwrite")
    content_before = content_fingerprint(DESTINATION_DISK)
    contract = source_contract()
    source_before = dict(contract["source_hashes"])
    imported, cvar_evidence = import_all_modules(contract)
    if not LIBRARY.save_directory(DESTINATION, only_if_is_dirty=False, recursive=True):
        fail("could not save scratch native assets")
    result = validate_imported(imported, contract)
    source_after = source_contract()["source_hashes"]
    content_after = content_fingerprint(DESTINATION_DISK)
    if source_after != source_before:
        fail("source RuntimePrep v002 changed during native scratch import")
    if content_after != content_before:
        changed = sorted(set(content_before) ^ set(content_after))
        changed.extend(sorted(
            key for key in set(content_before) & set(content_after)
            if content_before[key] != content_after[key]
        ))
        fail("content outside scratch destination changed: " + repr(changed[:20]))
    output = {
        "$schema": "lineboss/onefactory/press/material-flow-runtimeprep-v002/legacy-fbx-factory-scratch/v1",
        "generated_utc": now(),
        "status": "PASS__MATERIAL_FLOW_V002_NATIVE_LEGACY_FBX_FACTORY_SCRATCH",
        "destination_namespace": DESTINATION,
        "source_runtimeprep": str(SOURCE),
        "source_hashes": source_before,
        "import_policy": {
            "native_importer": "Unreal 5.8 legacy FbxFactory",
            "combine_meshes": False,
            "convert_scene": True,
            "convert_scene_unit": True,
            "transform_vertex_to_absolute": False,
            "bake_pivot_in_vertex": False,
            "auto_generate_collision": False,
            "remove_degenerates": False,
            "nanite": False,
            "imported_materials": False,
            "imported_textures": False,
        },
        "interchange_feature_flag": cvar_evidence,
        "source_payload_triangles": 3792,
        "native_mesh_count": result["native_meshes"],
        "native_payload_triangles": result["native_triangles"],
        "modules": result["modules"],
        "source_unchanged": True,
        "content_outside_scratch_unchanged": True,
        "map_opened_by_script": False,
        "map_saved_by_script": False,
        "promotion_authorized": False,
        "next_gate": "material/actor integration only after separate production import lane",
    }
    write_once(RECEIPT, output)
    return output


try:
    outcome = main()
    unreal.log("MATERIAL_FLOW_V002_LEGACY_FBX_FACTORY_SCRATCH_PASS=" + str(RECEIPT))
except Exception as error:
    payload = {
        "$schema": "lineboss/onefactory/press/material-flow-runtimeprep-v002/legacy-fbx-factory-scratch/v1",
        "generated_utc": now(),
        "status": "FAIL__MATERIAL_FLOW_V002_NATIVE_LEGACY_FBX_FACTORY_SCRATCH",
        "error": str(error),
        "traceback": traceback.format_exc(),
        "destination_namespace": DESTINATION,
        "map_opened_by_script": False,
        "map_saved_by_script": False,
        "promotion_authorized": False,
    }
    try:
        if not FAILURE.exists():
            write_once(FAILURE, payload)
    finally:
        unreal.log_error("MATERIAL_FLOW_V002_LEGACY_FBX_FACTORY_SCRATCH_FAIL=" + str(error))
    raise
finally:
    unreal.SystemLibrary.quit_editor()
