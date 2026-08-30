"""Measure legacy FbxFactory axis options before asking for another source export.

This is a disposable native-Unreal probe.  It imports the full S01 coil module
and the feed bridge under four explicit legacy option combinations, then
measures their source LOD bounds.  It neither opens/saves a map nor touches
the production material-flow namespace.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
EXPECTED_PROJECT = Path(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8").resolve()
SOURCE = PROJECT / "ArtSource/Claude_PressShop_MaterialFlowPack_RuntimePrep_v002"
STATS = SOURCE / "runtime_prep_stats_v002.json"
DESTINATION = (
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/_Scratch/"
    "MaterialFlowPack_v002_LegacyAxisProbe_v001"
)
DESTINATION_DISK = PROJECT / "Content" / Path(DESTINATION.removeprefix("/Game/"))
AUDIT = (PROJECT / "Saved/Audits/OneFactory/Press/MaterialFlowPackRuntimePrep_v002/"
         "legacy_axis_probe_v001.json")
FAILURE = AUDIT.with_name("legacy_axis_probe_v001_failure.json")
CV = "Interchange.FeatureFlags.Import.FBX"
LIBRARY = unreal.EditorAssetLibrary
MESH_EDITOR = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)

VARIANTS = {
    "convert_scene_true__front_x_false": {"convert_scene": True, "force_front_x_axis": False},
    "convert_scene_true__front_x_true": {"convert_scene": True, "force_front_x_axis": True},
    "convert_scene_false__front_x_false": {"convert_scene": False, "force_front_x_axis": False},
    "convert_scene_false__front_x_true": {"convert_scene": False, "force_front_x_axis": True},
}
TARGETS = {
    "SM_CA_MW_PT_S01CoilCart_v001",
    "SM_CA_MW_PT_S01FeedBridge_v001",
}


def now():
    return datetime.now(timezone.utc).isoformat()


def fail(message):
    raise RuntimeError("MATERIAL_FLOW_V002_LEGACY_AXIS_PROBE_FAIL: " + message)


def vector(value):
    return [round(float(value.x), 5), round(float(value.y), 5), round(float(value.z), 5)]


def bounds(mesh):
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
        fail("could not measure " + mesh.get_name())
    box = dynamic_mesh.get_mesh_bounding_box()
    return {"min": vector(box.min), "max": vector(box.max)}


def raw_slots(mesh):
    return [str(slot.get_editor_property("material_slot_name"))
            for slot in mesh.get_editor_property("static_materials")]


def make_task(source: Path, destination: str, variant: dict):
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(source),
        "destination_path": destination,
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
        "convert_scene": variant["convert_scene"],
        "convert_scene_unit": True,
        "force_front_x_axis": variant["force_front_x_axis"],
        "transform_vertex_to_absolute": False,
        "bake_pivot_in_vertex": False,
        "generate_lightmap_u_vs": False,
        "auto_generate_collision": False,
        "remove_degenerates": False,
        "build_nanite": False,
        "reorder_material_to_fbx_order": True,
    })
    factory = unreal.FbxFactory()
    factory.set_editor_property("asset_import_task", task)
    task.set_editor_property("factory", factory)
    task.set_editor_property("options", options)
    return task


def semantic_from_asset(mesh, specs):
    name = str(mesh.get_name())
    for semantic in specs:
        if name.endswith(semantic):
            return semantic
    triangles = int(mesh.get_num_triangles(0))
    candidates = [semantic for semantic, spec in specs.items()
                  if triangles == int(spec["triangles"])]
    if len(candidates) != 1:
        fail("cannot identify probe asset {}: {}".format(name, candidates))
    return candidates[0]


def import_variant(name, variant, modules, specs):
    destination = DESTINATION + "/" + name
    rows = []
    # Full CoilAssembly gives the mover, while the bridge gives an asymmetric
    # static flow/vertical sentinel.  Both use the exact same native pathway.
    for module_name in ("FeedCoilAssembly", "S01FeedBridge"):
        module = modules[module_name]
        task = make_task(SOURCE / module["file"], destination, variant)
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        paths = [str(path) for path in (task.get_editor_property("imported_object_paths") or [])]
        if len(paths) != len(module["meshes"]):
            fail("{}:{} child count drift {}".format(name, module_name, paths))
        for path in paths:
            mesh = unreal.load_asset(path)
            if not isinstance(mesh, unreal.StaticMesh):
                fail("{} imported non-static asset {}".format(name, path))
            semantic = semantic_from_asset(mesh, module["meshes"])
            if semantic not in TARGETS:
                continue
            data = mesh.get_editor_property("asset_import_data")
            rows.append({
                "semantic_mesh": semantic,
                "object_path": str(mesh.get_path_name()),
                "bounds_cm": bounds(mesh),
                "triangles": int(mesh.get_num_triangles(0)),
                "uv_channels": int(MESH_EDITOR.get_num_uv_channels(mesh, 0)),
                "slots": raw_slots(mesh),
                "asset_import_data_class": str(data.get_class().get_name()),
                "persisted_convert_scene": bool(data.get_editor_property("convert_scene")),
                "persisted_force_front_x_axis": bool(data.get_editor_property("force_front_x_axis")),
                "persisted_transform_vertex_to_absolute": bool(data.get_editor_property("transform_vertex_to_absolute")),
                "persisted_bake_pivot_in_vertex": bool(data.get_editor_property("bake_pivot_in_vertex")),
                "expected_authored_ue_bounds_cm": specs[semantic]["expected_ue_aabb_cm"],
            })
    if {row["semantic_mesh"] for row in rows} != TARGETS:
        fail("{} target selection drift: {}".format(name, rows))
    return rows


def main():
    if PROJECT != EXPECTED_PROJECT:
        fail("wrong project")
    if DESTINATION_DISK.exists() or LIBRARY.does_directory_exist(DESTINATION):
        fail("probe destination already exists")
    if AUDIT.exists() or FAILURE.exists():
        fail("probe evidence already exists")
    if not STATS.is_file():
        fail("stats missing")
    stats = json.loads(STATS.read_text(encoding="utf-8"))
    modules = stats["modules"]
    specs = {}
    for module in modules.values():
        specs.update(module["meshes"])
    if not TARGETS <= set(specs):
        fail("target source spec absent")
    previous = int(unreal.SystemLibrary.get_console_variable_int_value(CV))
    if previous not in (0, 1):
        fail("unexpected Interchange cvar=" + str(previous))
    cvar = {"name": CV, "previous": previous, "disabled": None, "restored": None}
    probe_rows = {}
    import_error = None
    try:
        unreal.SystemLibrary.execute_console_command(None, CV + " 0")
        cvar["disabled"] = int(unreal.SystemLibrary.get_console_variable_int_value(CV))
        if cvar["disabled"] != 0:
            fail("could not force legacy FBX factory")
        for name, variant in VARIANTS.items():
            probe_rows[name] = {
                "requested_options": variant,
                "observations": import_variant(name, variant, modules, specs),
            }
    except Exception as error:
        import_error = error
    finally:
        unreal.SystemLibrary.execute_console_command(None, "{} {}".format(CV, previous))
        cvar["restored"] = int(unreal.SystemLibrary.get_console_variable_int_value(CV))
    if cvar["restored"] != previous:
        fail("could not restore Interchange feature flag")
    if import_error is not None:
        raise import_error
    if not LIBRARY.save_directory(DESTINATION, only_if_is_dirty=False, recursive=True):
        fail("could not save probe assets")
    payload = {
        "$schema": "lineboss/onefactory/press/material-flow-runtimeprep-v002/legacy-axis-options-probe/v1",
        "generated_utc": now(),
        "status": "PASS__NATIVE_LEGACY_FBX_AXIS_OPTION_MEASUREMENTS",
        "probe_namespace": DESTINATION,
        "native_importer": "Unreal 5.8 legacy FbxFactory",
        "interchange_feature_flag": cvar,
        "fixed_native_pivot_settings": {
            "combine_meshes": False,
            "convert_scene_unit": True,
            "transform_vertex_to_absolute": False,
            "bake_pivot_in_vertex": False,
            "import_uniform_scale": 1.0,
        },
        "variants": probe_rows,
        "map_opened_by_script": False,
        "map_saved_by_script": False,
        "promotion_authorized": False,
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


try:
    main()
    unreal.log("MATERIAL_FLOW_V002_LEGACY_AXIS_PROBE_PASS=" + str(AUDIT))
except Exception as error:
    FAILURE.parent.mkdir(parents=True, exist_ok=True)
    if not FAILURE.exists():
        FAILURE.write_text(json.dumps({
            "status": "FAIL__NATIVE_LEGACY_FBX_AXIS_OPTION_MEASUREMENTS",
            "error": str(error),
            "generated_utc": now(),
            "probe_namespace": DESTINATION,
        }, indent=2) + "\n", encoding="utf-8")
    unreal.log_error("MATERIAL_FLOW_V002_LEGACY_AXIS_PROBE_FAIL=" + str(error))
    raise
finally:
    unreal.SystemLibrary.quit_editor()
