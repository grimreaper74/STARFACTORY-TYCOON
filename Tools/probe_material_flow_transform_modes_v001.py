"""Isolated, non-map A/B test for MaterialFlow FBX transform semantics.

It imports the four-mesh S01 FeedCoilAssembly twice under a throwaway probe
namespace, once per measured transform mode, and records the resulting mesh
bounds/import settings.  It never touches the approved native namespaces or a
map.  The disposable probe packages are retained for recoverable relocation
after the diagnostic is read.
"""

from __future__ import annotations

import json
from pathlib import Path

import unreal


PROJECT_ROOT = Path(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8")
SOURCE_FBX = (PROJECT_ROOT / "ArtSource/Claude_PressShop_MaterialFlowPack_RuntimePrep_v001/"
              "CA_PTA_S01_FeedCoilAssembly_LOD0.fbx")
DESTINATION = "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowTransformProbe_v001"
OUT = (PROJECT_ROOT / "Saved/Audits/OneFactory/Press/MaterialFlowPackRuntimePrep_v001/"
       "transform_mode_probe_v001.json")
MODES = {
    "local_pivot_scaled": {"transform_vertex_to_absolute": False, "import_uniform_scale": 100.0},
    "absolute_default_scale": {"transform_vertex_to_absolute": True, "import_uniform_scale": 1.0},
}
PROPERTIES = (
    "import_uniform_scale", "convert_scene", "convert_scene_unit",
    "transform_vertex_to_absolute", "bake_pivot_in_vertex",
)


def fail(message: str) -> None:
    raise RuntimeError("MaterialFlow transform-mode probe failed: {}".format(message))


def vector(value):
    return [round(float(value.x), 6), round(float(value.y), 6), round(float(value.z), 6)]


def import_mode(label: str, config: dict) -> dict:
    destination = DESTINATION + "/" + label
    if unreal.EditorAssetLibrary.does_directory_exist(destination):
        fail("probe destination already exists: {}".format(destination))
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True,
        "import_materials": False,
        "import_textures": False,
        "import_as_skeletal": False,
        "automated_import_should_detect_type": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    static_data = options.static_mesh_import_data
    static_data.set_editor_properties({
        "combine_meshes": False,
        "auto_generate_collision": False,
        "generate_lightmap_u_vs": False,
        "remove_degenerates": True,
        "import_uniform_scale": config["import_uniform_scale"],
        "convert_scene": True,
        "convert_scene_unit": True,
        "force_front_x_axis": False,
        "transform_vertex_to_absolute": config["transform_vertex_to_absolute"],
        "bake_pivot_in_vertex": False,
    })
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(SOURCE_FBX),
        "destination_path": destination,
        "automated": True,
        "replace_existing": False,
        "save": True,
        "options": options,
    })
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported = list(task.get_editor_property("imported_object_paths") or [])
    if len(imported) != 4:
        fail("{} imported {} objects rather than four: {}".format(label, len(imported), imported))
    result = {}
    for object_path in sorted(imported):
        mesh = unreal.load_asset(object_path)
        if mesh is None or not isinstance(mesh, unreal.StaticMesh):
            fail("{} did not resolve to a StaticMesh".format(object_path))
        bounds = mesh.get_bounding_box()
        import_data = mesh.get_editor_property("asset_import_data")
        import_settings = {}
        for prop in PROPERTIES:
            try:
                import_settings[prop] = import_data.get_editor_property(prop)
            except Exception as error:
                # UE 5.8 may expose InterchangeAssetImportData rather than
                # FbxStaticMeshImportData.  Bounds are still the purpose of
                # this diagnostic, so record the metadata limitation.
                import_settings[prop] = "UNAVAILABLE: {}".format(error)
        result[mesh.get_name()] = {
            "object_path": object_path,
            "bounds": {"min": vector(bounds.min), "max": vector(bounds.max)},
            "dimensions": vector(bounds.max - bounds.min),
            "import_settings": import_settings,
        }
    return result


if not SOURCE_FBX.is_file():
    fail("source FBX is missing")
if OUT.exists():
    fail("probe output already exists: {}".format(OUT))
if unreal.EditorAssetLibrary.does_directory_exist(DESTINATION):
    existing = list(unreal.EditorAssetLibrary.list_assets(
        DESTINATION, recursive=True, include_folder=False))
    if existing:
        fail("probe namespace already contains assets: {}".format(sorted(existing)))

rows = {label: import_mode(label, config) for label, config in MODES.items()}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "$schema": "lineboss/onefactory/press/material-flow-transform-mode-probe/v1",
    "status": "PASS__ISOLATED_A_B_IMPORT_COMPLETE",
    "source_fbx": str(SOURCE_FBX),
    "source_content_writes": [],
    "map_opened_by_script": False,
    "map_saved_by_script": False,
    "probe_destination": DESTINATION,
    "modes": rows,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("LINE_BOSS_MATERIAL_FLOW_TRANSFORM_MODE_PROBE_PASS")
unreal.SystemLibrary.quit_editor()
