"""Guarded native UE intake for Claude's open-frame S03-S06 silhouette pack.

The source package is immutable evidence.  This script imports only its four
new frames into an isolated OneFactory namespace, proves raw FBX and imported
mesh contracts, binds existing native semantic materials, and emits a receipt.
It intentionally does not open/save a map or wire the assets into gameplay;
that later C++ integration is separately gated.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import traceback
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
EXPECTED_PROJECT = Path(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8").resolve()
SOURCE = PROJECT / "ArtSource/Claude_PressShop_OpenFrameSilhouette_v001"
MANIFEST = SOURCE / "openframe_manifest.json"
RAW_PROBE = SOURCE / "fbx_raw_probe.py"
DEST = "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/OpenFrameSilhouette_v001"
MESH_DEST = DEST + "/Meshes"
SCRATCH_DEST = DEST + "/_ImportScratch"
AUDIT_DIR = PROJECT / "Saved/Audits/OneFactory/Press/OpenFrameSilhouetteNative_v001"
RECEIPT = AUDIT_DIR / "native_import_receipt_v001.json"
FAILURE = AUDIT_DIR / "native_import_failure_v001.json"
STAGE_RECEIPT = (PROJECT / "Saved/Audits/OneFactory/Press/"
                 "S03S06StagePackRuntimePrep_v001/import_receipt.json")
TOLERANCE_CM = 0.5

MATERIALS = {
    "CA_MW_FoundryCharcoal": (
        "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
        "SharedTrainModules_v003/Materials/MI_CA_MW_PT_FoundryCharcoal_v001."
        "MI_CA_MW_PT_FoundryCharcoal_v001"),
    "CA_MW_CairnwellGreen": (
        "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
        "SharedTrainModules_v003/Materials/MI_CA_MW_PT_CairnwellGreen_v001."
        "MI_CA_MW_PT_CairnwellGreen_v001"),
    "CA_MW_WorkedSteel": (
        "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
        "SharedTrainModules_v003/Materials/MI_CA_MW_PT_WorkedSteel_v001."
        "MI_CA_MW_PT_WorkedSteel_v001"),
    "CA_MW_SafetyYellow": (
        "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
        "SharedTrainModules_v003/Materials/MI_CA_MW_PT_SafetyYellow_v001."
        "MI_CA_MW_PT_SafetyYellow_v001"),
}

LIBRARY = unreal.EditorAssetLibrary
ASSET_TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
MESH_EDITOR = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)


def fail(message):
    raise RuntimeError("OPENFRAME_SILHOUETTE_NATIVE_IMPORT_V001_FAIL: " + message)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def object_path(folder, name):
    return "{0}/{1}.{1}".format(folder, name)


def vector_list(value):
    return [round(float(value.x), 4), round(float(value.y), 4), round(float(value.z), 4)]


def bounds_cm(mesh):
    dynamic_mesh = unreal.DynamicMesh()
    options = unreal.GeometryScriptCopyMeshFromAssetOptions()
    lod = unreal.GeometryScriptMeshReadLOD()
    lod.set_editor_properties({
        "lod_type": unreal.GeometryScriptLODType.SOURCE_MODEL,
        "lod_index": 0,
    })
    dynamic_mesh, outcome = unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(
        mesh, dynamic_mesh, options, lod, False)
    if outcome != unreal.GeometryScriptOutcomePins.SUCCESS:
        fail("GeometryScript bounds read failed for " + mesh.get_name())
    box = dynamic_mesh.get_mesh_bounding_box()
    return {"min": vector_list(box.min), "max": vector_list(box.max)}


def dimensions(box):
    return [round(float(box["max"][i]) - float(box["min"][i]), 4)
            for i in range(3)]


def load_raw_probe():
    if not RAW_PROBE.is_file():
        fail("source raw FBX probe is absent")
    spec = importlib.util.spec_from_file_location("openframe_raw_probe", RAW_PROBE)
    if spec is None or spec.loader is None:
        fail("could not load source raw FBX probe")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_contract():
    if PROJECT != EXPECTED_PROJECT:
        fail("wrong project path")
    if str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory":
        fail("wrong game")
    if not MANIFEST.is_file() or not STAGE_RECEIPT.is_file():
        fail("source manifest or shared stage receipt is absent")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    modules = manifest.get("modules", {})
    if set(modules) != {"S03", "S04", "S05", "S06"}:
        fail("source module inventory drift")
    required_slots = ["CA_MW_FoundryCharcoal", "CA_MW_CairnwellGreen",
                      "CA_MW_WorkedSteel", "CA_MW_SafetyYellow"]
    if manifest.get("slot_order") != required_slots:
        fail("source material-slot order drift")
    stage = json.loads(STAGE_RECEIPT.read_text(encoding="utf-8"))
    if stage.get("status") != "PASS__TEXTURED_STAGEPACK_V001_IMPORTED_AT_RECEIPTED_UNREAL_SCALE":
        fail("shared stage material receipt is not an approved pass")
    if dict(stage.get("materials_by_semantic_slot", {})) and not set(MATERIALS).issubset(
            set(stage["materials_by_semantic_slot"])):
        fail("shared stage receipt does not own the required semantic materials")
    for slot, path in MATERIALS.items():
        material = unreal.load_asset(path)
        if not isinstance(material, unreal.MaterialInterface):
            fail("native semantic material does not resolve: " + slot)

    raw_probe = load_raw_probe()
    specs = {}
    for station, row in sorted(modules.items()):
        fbx = SOURCE / str(row.get("file", ""))
        if not fbx.is_file() or sha256(fbx) != row.get("fbx_sha256"):
            fail("source FBX hash drift: " + station)
        if list(row.get("material_slots", [])) != required_slots:
            fail("source material slots drift: " + station)
        raw = raw_probe.summarise(str(fbx))
        settings = raw.get("global_settings", {})
        if settings.get("UnitScaleFactor") != 1.0 or settings.get("OriginalUnitScaleFactor") != 1.0:
            fail("raw FBX unit scale drift: " + station)
        geometries = raw.get("geometries", [])
        models = raw.get("models", [])
        if len(geometries) != 1 or len(models) != 1 or geometries[0].get("control_points", 0) <= 0:
            fail("raw FBX geometry/node inventory drift: " + station)
        model = models[0]
        if (model.get("Lcl Translation") != [0.0, 0.0, 0.0]
                or model.get("Lcl Rotation") != [0.0, 0.0, 0.0]
                or model.get("Lcl Scaling") != [1.0, 1.0, 1.0]
                or model.get("GeometricTranslation") != [0.0, 0.0, 0.0]
                or model.get("GeometricScaling") != [1.0, 1.0, 1.0]):
            fail("raw FBX node-transform drift: " + station)
        min_v = geometries[0].get("raw_aabb_min")
        max_v = geometries[0].get("raw_aabb_max")
        if not min_v or not max_v:
            fail("raw FBX AABB missing: " + station)
        # Blender's raw FBX Y is up. UE's Convert Scene must yield X/Z/Y.
        expected_dims = [round((max_v[0] - min_v[0]), 4),
                         round((max_v[2] - min_v[2]), 4),
                         round((max_v[1] - min_v[1]), 4)]
        source_aabb = row.get("local_aabb_evaluated_m", {})
        source_dims = [round(100.0 * (source_aabb["max"][i] - source_aabb["min"][i]), 4)
                       for i in range(3)]
        if any(abs(expected_dims[i] - source_dims[i]) > TOLERANCE_CM for i in range(3)):
            fail("raw FBX dimensions do not match manifest: " + station)
        name = str(row.get("object", ""))
        if not name.startswith("SM_CA_MW_PT_OpenFrame_"):
            fail("source semantic model name drift: " + station)
        specs[station] = {
            "station": station,
            "name": name,
            "source": fbx,
            "sha256": row["fbx_sha256"],
            "triangles": int(row["evaluated_export_triangles"]),
            "expected_dimensions_cm": source_dims,
            "material_slots": required_slots,
            "raw_control_points": int(geometries[0]["control_points"]),
            "raw_geometry_name": geometries[0]["name"],
            "raw_model_name": model["name"],
        }
    return manifest, specs


def mesh_task(source):
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(source),
        "destination_path": SCRATCH_DEST,
        "automated": True,
        "async_": False,
        "replace_existing": False,
        "replace_existing_settings": False,
        "save": False,
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
        "combine_meshes": False,
        "convert_scene": True,
        "convert_scene_unit": True,
        "force_front_x_axis": False,
        "transform_vertex_to_absolute": False,
        "bake_pivot_in_vertex": False,
        "generate_lightmap_u_vs": False,
        "auto_generate_collision": False,
        "remove_degenerates": False,
        "import_uniform_scale": 1.0,
        "build_nanite": False,
    })
    factory = unreal.FbxFactory()
    factory.set_editor_property("asset_import_task", task)
    task.factory = factory
    task.options = options
    return task


def import_meshes(specs):
    tasks = [(station, mesh_task(spec["source"]))
             for station, spec in sorted(specs.items())]
    ASSET_TOOLS.import_asset_tasks([task for _, task in tasks])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    meshes = {}
    for station, task in tasks:
        paths = [str(path) for path in task.get_editor_property("imported_object_paths")]
        if len(paths) != 1:
            fail("native import did not produce exactly one mesh: {}: {}".format(station, paths))
        mesh = unreal.load_asset(paths[0])
        if not isinstance(mesh, unreal.StaticMesh):
            fail("native import did not resolve StaticMesh: " + station)
        meshes[station] = mesh
    renames = [unreal.AssetRenameData(meshes[station], MESH_DEST, specs[station]["name"])
               for station in sorted(specs)]
    if not ASSET_TOOLS.rename_assets(renames):
        fail("native semantic mesh rename failed")
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    leftovers = list(LIBRARY.list_assets(SCRATCH_DEST, recursive=True, include_folder=False))
    if leftovers:
        fail("native scratch packages remain after semantic rename")
    output = {station: unreal.load_asset(object_path(MESH_DEST, spec["name"]))
              for station, spec in specs.items()}
    if not all(isinstance(mesh, unreal.StaticMesh) for mesh in output.values()):
        fail("native renamed mesh resolution drift")
    return output


def import_policy(mesh):
    data = mesh.get_editor_property("asset_import_data")
    return {
        "combine_meshes": bool(data.get_editor_property("combine_meshes")),
        "convert_scene": bool(data.get_editor_property("convert_scene")),
        "convert_scene_unit": bool(data.get_editor_property("convert_scene_unit")),
        "force_front_x_axis": bool(data.get_editor_property("force_front_x_axis")),
        "transform_vertex_to_absolute": bool(data.get_editor_property("transform_vertex_to_absolute")),
        "bake_pivot_in_vertex": bool(data.get_editor_property("bake_pivot_in_vertex")),
        "auto_generate_collision": bool(data.get_editor_property("auto_generate_collision")),
        "remove_degenerates": bool(data.get_editor_property("remove_degenerates")),
        "import_uniform_scale": float(data.get_editor_property("import_uniform_scale")),
    }


def configure_and_verify(meshes, specs):
    expected_policy = {
        "combine_meshes": False, "convert_scene": True, "convert_scene_unit": True,
        "force_front_x_axis": False, "transform_vertex_to_absolute": False,
        "bake_pivot_in_vertex": False, "auto_generate_collision": False,
        "remove_degenerates": False, "import_uniform_scale": 1.0,
    }
    result = {}
    for station, spec in sorted(specs.items()):
        mesh = meshes[station]
        expected_path = object_path(MESH_DEST, spec["name"])
        if mesh.get_path_name() != expected_path:
            fail("native mesh path drift: " + station)
        if int(mesh.get_num_lods()) != 1:
            fail("native LOD inventory drift: " + station)
        if int(mesh.get_num_triangles(0)) != spec["triangles"]:
            fail("native payload triangle drift: {} {} vs {}".format(
                station, mesh.get_num_triangles(0), spec["triangles"]))
        if int(MESH_EDITOR.get_simple_collision_count(mesh)) or int(MESH_EDITOR.get_convex_collision_count(mesh)):
            fail("native collision unexpectedly exists: " + station)
        if bool(MESH_EDITOR.get_nanite_settings(mesh).get_editor_property("enabled")):
            fail("native Nanite unexpectedly enabled: " + station)
        actual_bounds = bounds_cm(mesh)
        actual_dims = dimensions(actual_bounds)
        if any(abs(actual_dims[i] - spec["expected_dimensions_cm"][i]) > TOLERANCE_CM
               for i in range(3)):
            fail("native scale/axis dimensions drift: {} {} vs {}".format(
                station, actual_dims, spec["expected_dimensions_cm"]))
        slots = list(mesh.get_editor_property("static_materials"))
        names = [str(slot.get_editor_property("material_slot_name")) for slot in slots]
        if names != spec["material_slots"]:
            fail("native semantic material-slot drift: {} {}".format(station, names))
        assigned = []
        for index, slot_name in enumerate(names):
            target = unreal.load_asset(MATERIALS[slot_name])
            if not isinstance(target, unreal.MaterialInterface):
                fail("native material target no longer resolves: " + slot_name)
            mesh.set_material(index, target)
            assigned.append(target.get_path_name())
        uv_channels = int(MESH_EDITOR.get_num_uv_channels(mesh, 0))
        if uv_channels < 1:
            fail("native mesh has no UV0: " + station)
        mesh.set_editor_properties({
            "light_map_coordinate_index": 0,
            "light_map_resolution": 64,
        })
        if not LIBRARY.save_loaded_asset(mesh, only_if_is_dirty=False):
            fail("native mesh save failed: " + station)
        policy = import_policy(mesh)
        if policy != expected_policy:
            fail("native import policy drift: {} {}".format(station, policy))
        result[station] = {
            "path": mesh.get_path_name(),
            "triangles": int(mesh.get_num_triangles(0)),
            "bounds_cm": actual_bounds,
            "dimensions_cm": actual_dims,
            "material_slots": names,
            "materials": assigned,
            "uv_channels": uv_channels,
            "legacy_import_data": policy,
        }
    return result


def main():
    evidence = {
        "$schema": "lineboss/onefactory/press/openframe-silhouette-v001/native-import-v001/v1",
        "generated_utc": utc_now(),
        "destination": DEST,
        "map_opened_by_script": False,
        "map_saved_by_script": False,
        "source_assets_mutated": False,
        "content_writes": [DEST],
        "integration_authorized": False,
    }
    try:
        manifest, specs = source_contract()
        evidence.update({
            "source_manifest_sha256": sha256(MANIFEST),
            "source_fbx": {station: {"path": str(spec["source"]), "sha256": spec["sha256"]}
                           for station, spec in specs.items()},
        })
        if RECEIPT.exists():
            fail("prior successful receipt exists; refusing overwrite")
        if LIBRARY.does_directory_exist(DEST):
            fail("fresh destination namespace already exists")
        meshes = import_meshes(specs)
        rows = configure_and_verify(meshes, specs)
        registry = set(str(item) for item in LIBRARY.list_assets(
            DEST, recursive=True, include_folder=False))
        expected_registry = {object_path(MESH_DEST, spec["name"]) for spec in specs.values()}
        if registry != expected_registry:
            fail("native package closure drift: {} vs {}".format(registry, expected_registry))
        evidence.update({
            "status": "PASS__OPENFRAME_SILHOUETTE_V001_NATIVE_IMPORT",
            "native_mesh_count": len(rows),
            "native_payload_triangles": sum(row["triangles"] for row in rows.values()),
            "native_assets": sorted(registry),
            "native_recipe": {
                "importer": "Unreal 5.8 legacy FbxFactory",
                "combine_meshes": False,
                "convert_scene": True,
                "convert_scene_unit": True,
                "transform_vertex_to_absolute": False,
                "bake_pivot_in_vertex": False,
                "collision": "none authored/imported",
                "nanite": False,
            },
            "meshes": rows,
        })
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        RECEIPT.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        unreal.log("OPENFRAME_SILHOUETTE_NATIVE_IMPORT_V001_PASS=" + str(RECEIPT))
    except Exception as error:
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        failure = {
            **evidence,
            "status": "FAIL_CLOSED__OPENFRAME_SILHOUETTE_V001_NATIVE_IMPORT",
            "error": str(error),
            "traceback": traceback.format_exc(),
            "partial_native_assets_preserved": list(LIBRARY.list_assets(
                DEST, recursive=True, include_folder=False)) if LIBRARY.does_directory_exist(DEST) else [],
        }
        FAILURE.write_text(json.dumps(failure, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        unreal.log_error("OPENFRAME_SILHOUETTE_NATIVE_IMPORT_V001_FAIL=" + str(error))
        raise
    finally:
        unreal.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main()
