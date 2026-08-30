"""Disposable native FBX-axis probe for the pivot-safe SteamHero v002 exports.

No map is opened and no imported package is saved.  The only durable output is
one JSON measurement under Saved/Audits, so the final import recipe is chosen
from UE 5.8's actual vertex output rather than an assumed axis convention.
"""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
SOURCE = PROJECT / "ArtSource/Claude_PressShop_SteamHeroDetailPack_RuntimePrep_v002/CA_PTA_Hero_ReusedKitProps_LOD0.fbx"
ROOT = "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/_AxisProbeSteamHero_v002"
OUT = PROJECT / "Saved/Audits/OneFactory/Press/SteamHeroDetailPackRuntimePrep_v002/axis_probe_v002.json"
LIBRARY = unreal.EditorAssetLibrary


def fail(message):
    raise RuntimeError("STEAM_HERO_AXIS_PROBE_V002_FAIL: " + message)


def values(vector):
    return [round(float(vector.x), 5), round(float(vector.y), 5), round(float(vector.z), 5)]


def bounds(mesh):
    dynamic_mesh = unreal.DynamicMesh()
    options = unreal.GeometryScriptCopyMeshFromAssetOptions()
    lod = unreal.GeometryScriptMeshReadLOD()
    lod.set_editor_properties({"lod_type": unreal.GeometryScriptLODType.SOURCE_MODEL, "lod_index": 0})
    dynamic_mesh, outcome = unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(
        mesh, dynamic_mesh, options, lod, False)
    if outcome != unreal.GeometryScriptOutcomePins.SUCCESS:
        fail("GeometryScript read failure: " + mesh.get_name())
    box = dynamic_mesh.get_mesh_bounding_box()
    return {"min": values(box.min), "max": values(box.max)}


def import_probe(label, absolute, convert_scene):
    dest = ROOT + "/" + label
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(SOURCE), "destination_path": dest, "automated": True,
        "async_": False, "replace_existing": False,
        "replace_existing_settings": False, "save": False,
    })
    ui = unreal.FbxImportUI()
    ui.set_editor_properties({
        "import_mesh": True, "import_as_skeletal": False,
        "import_materials": False, "import_textures": False,
        "import_animations": False, "automated_import_should_detect_type": False,
        "create_physics_asset": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    data = ui.get_editor_property("static_mesh_import_data")
    data.set_editor_properties({
        "combine_meshes": False, "convert_scene": convert_scene,
        "convert_scene_unit": True, "force_front_x_axis": False,
        "transform_vertex_to_absolute": absolute, "bake_pivot_in_vertex": False,
        "generate_lightmap_u_vs": False, "auto_generate_collision": False,
        "remove_degenerates": False, "import_uniform_scale": 1.0,
        "build_nanite": False,
    })
    factory = unreal.FbxFactory()
    factory.set_editor_property("asset_import_task", task)
    task.factory = factory
    task.options = ui
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assets = [str(value) for value in task.get_editor_property("imported_object_paths")]
    if len(assets) != 2:
        fail("unexpected asset count for {}: {}".format(label, assets))
    rows = {}
    for path in assets:
        mesh = unreal.load_asset(path)
        if not isinstance(mesh, unreal.StaticMesh):
            fail("probe import is not a static mesh: " + path)
        import_data = mesh.get_editor_property("asset_import_data")
        rows[mesh.get_name()] = {
            "path": path, "triangles": int(mesh.get_num_triangles(0)),
            "bounds_cm": bounds(mesh),
            "legacy_import_data": {
                "convert_scene": bool(import_data.get_editor_property("convert_scene")),
                "transform_vertex_to_absolute": bool(import_data.get_editor_property("transform_vertex_to_absolute")),
            },
        }
    return rows


try:
    if OUT.exists():
        fail("refusing to overwrite prior axis probe")
    if not SOURCE.is_file():
        fail("v002 source FBX absent")
    if LIBRARY.does_directory_exist(ROOT):
        fail("probe destination already exists")
    variants = {
        "absolute_convert_scene": import_probe("AbsoluteConvertScene", True, True),
        "relative_convert_scene": import_probe("RelativeConvertScene", False, True),
        "absolute_raw_scene": import_probe("AbsoluteRawScene", True, False),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "$schema": "lineboss/onefactory/press/steamhero-axis-probe-v002/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__DISPOSABLE_STEAMHERO_FBX_AXIS_PROBE",
        "source": str(SOURCE), "variants": variants,
        "map_opened_or_saved": False, "content_writes": [],
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    unreal.log("STEAM_HERO_AXIS_PROBE_V002_PASS=" + str(OUT))
finally:
    unreal.SystemLibrary.quit_editor()
