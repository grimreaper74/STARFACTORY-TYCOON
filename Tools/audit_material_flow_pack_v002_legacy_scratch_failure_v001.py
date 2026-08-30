"""Read-only diagnostic for the failed MaterialFlow v002 legacy-FBX scratch."""

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
    "MaterialFlowPack_v002_LegacyFbxFactory_v001"
)
AUDIT = (PROJECT / "Saved/Audits/OneFactory/Press/MaterialFlowPackRuntimePrep_v002/"
         "legacy_fbx_factory_scratch_v001_diagnostics.json")
LIBRARY = unreal.EditorAssetLibrary
MESH_EDITOR = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
TOLERANCE_CM = 0.25


def fail(message):
    raise RuntimeError("MATERIAL_FLOW_V002_LEGACY_SCRATCH_DIAGNOSTIC_FAIL: " + message)


def now():
    return datetime.now(timezone.utc).isoformat()


def vector(value):
    return [round(float(value.x), 5), round(float(value.y), 5), round(float(value.z), 5)]


def normalize(name):
    return name[:-4] if len(name) >= 4 and name[-4] == "." and name[-3:].isdigit() else name


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
        fail("GeometryScript source LOD copy failed for {}: {}".format(mesh.get_name(), outcome))
    box = dynamic_mesh.get_mesh_bounding_box()
    return {"min": vector(box.min), "max": vector(box.max)}


def close(actual, expected):
    return len(actual) == len(expected) and all(
        abs(float(actual[index]) - float(expected[index])) <= TOLERANCE_CM
        for index in range(len(expected))
    )


def source_specs(stats):
    result = {}
    for module_name, module in stats["modules"].items():
        for semantic_name, spec in module["meshes"].items():
            result[semantic_name] = {"module": module_name, **spec}
    if len(result) != 10:
        fail("expected ten source specs")
    return result


def row(mesh, specs):
    raw_slots = [str(slot.get_editor_property("material_slot_name"))
                 for slot in mesh.get_editor_property("static_materials")]
    normalized_slots = [normalize(slot) for slot in raw_slots]
    native_bounds = bounds(mesh)
    triangles = int(mesh.get_num_triangles(0))
    candidate_rows = []
    for semantic_name, spec in sorted(specs.items()):
        expected = spec["expected_ue_aabb_cm"]
        triangle_match = triangles == int(spec["triangles"])
        bounds_match = close(native_bounds["min"], expected["min"]) and close(native_bounds["max"], expected["max"])
        slots_match = normalized_slots == list(spec["material_slots"])
        if triangle_match or bounds_match or slots_match:
            candidate_rows.append({
                "semantic_mesh": semantic_name,
                "triangle_match": triangle_match,
                "bounds_match": bounds_match,
                "slots_match": slots_match,
                "expected_triangles": int(spec["triangles"]),
                "expected_bounds": expected,
                "expected_slots": list(spec["material_slots"]),
            })
    data = mesh.get_editor_property("asset_import_data")
    import_data = {"class": str(data.get_class().get_name())}
    for field in ("import_uniform_scale", "convert_scene", "convert_scene_unit", "force_front_x_axis",
                  "transform_vertex_to_absolute", "bake_pivot_in_vertex", "generate_lightmap_u_vs",
                  "auto_generate_collision", "remove_degenerates"):
        try:
            import_data[field] = data.get_editor_property(field)
        except Exception as error:
            import_data[field] = "UNAVAILABLE: " + str(error)
    return {
        "object_path": str(mesh.get_path_name()),
        "asset_name": str(mesh.get_name()),
        "triangles": triangles,
        "lod_count": int(mesh.get_num_lods()),
        "uv_channels": int(MESH_EDITOR.get_num_uv_channels(mesh, 0)),
        "source_lod_bounds_cm": native_bounds,
        "render_bounds_cm": {"min": vector(mesh.get_bounding_box().min), "max": vector(mesh.get_bounding_box().max)},
        "raw_slot_names": raw_slots,
        "normalized_slot_names": normalized_slots,
        "simple_collision_count": int(MESH_EDITOR.get_simple_collision_count(mesh)),
        "convex_collision_count": int(MESH_EDITOR.get_convex_collision_count(mesh)),
        "nanite_enabled": bool(MESH_EDITOR.get_nanite_settings(mesh).get_editor_property("enabled")),
        "asset_import_data": import_data,
        "candidate_comparisons": candidate_rows,
    }


try:
    if PROJECT != EXPECTED_PROJECT:
        fail("wrong project")
    if AUDIT.exists():
        fail("refusing to overwrite diagnostic receipt")
    if not STATS.is_file():
        fail("v002 stats missing")
    if not LIBRARY.does_directory_exist(DESTINATION):
        fail("failed scratch namespace is absent")
    specs = source_specs(json.loads(STATS.read_text(encoding="utf-8")))
    paths = sorted(str(path) for path in LIBRARY.list_assets(DESTINATION, recursive=True, include_folder=False))
    meshes = []
    non_mesh = []
    for path in paths:
        asset = unreal.load_asset(path)
        if isinstance(asset, unreal.StaticMesh):
            meshes.append(row(asset, specs))
        else:
            non_mesh.append({"path": path, "class": str(asset.get_class().get_name()) if asset else "None"})
    payload = {
        "$schema": "lineboss/onefactory/press/material-flow-runtimeprep-v002/legacy-fbx-factory-scratch-diagnostic/v1",
        "generated_utc": now(),
        "status": "PASS__READ_ONLY_LEGACY_SCRATCH_DIAGNOSTIC",
        "scratch_namespace": DESTINATION,
        "native_static_mesh_count": len(meshes),
        "native_non_static_assets": non_mesh,
        "meshes": meshes,
        "map_opened_by_script": False,
        "map_saved_by_script": False,
        "content_writes": [],
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    unreal.log("MATERIAL_FLOW_V002_LEGACY_SCRATCH_DIAGNOSTIC_PASS=" + str(AUDIT))
except Exception as error:
    unreal.log_error("MATERIAL_FLOW_V002_LEGACY_SCRATCH_DIAGNOSTIC_FAIL=" + str(error))
    raise
finally:
    unreal.SystemLibrary.quit_editor()
