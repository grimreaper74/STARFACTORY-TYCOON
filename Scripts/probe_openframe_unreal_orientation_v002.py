"""Corrected orientation probe: test an FBX import roll about UE's X axis.

v001 revealed the Python ``Rotator`` constructor order is roll, pitch, yaw.
Its intended roll trials therefore tested yaw.  This version preserves v001
and runs the actual roll variants in an isolated disposable namespace.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
SOURCE = PROJECT / "ArtSource/Claude_PressShop_OpenFrameSilhouette_v001"
MANIFEST = SOURCE / "openframe_manifest.json"
FBX = SOURCE / "CA_PTA_OpenFrame_S03_LOD0.fbx"
DEST = "/Game/Developer/Validation/OpenFrameOrientationProbe_v002"
AUDIT = PROJECT / "Saved/Audits/OneFactory/Press/OpenFrameOrientationProbe_v002.json"
LIBRARY = unreal.EditorAssetLibrary
ASSET_TOOLS = unreal.AssetToolsHelpers.get_asset_tools()

VARIANTS = {
    "roll_plus_90": 90.0,
    "roll_minus_90": -90.0,
}


def fail(message: str) -> None:
    raise RuntimeError("OPENFRAME_ORIENTATION_PROBE_V002_FAIL: " + message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
        fail("GeometryScript bounds copy failed")
    box = dynamic_mesh.get_mesh_bounding_box()
    minimum = [round(float(box.min.x), 4), round(float(box.min.y), 4), round(float(box.min.z), 4)]
    maximum = [round(float(box.max.x), 4), round(float(box.max.y), 4), round(float(box.max.z), 4)]
    return {
        "min": minimum,
        "max": maximum,
        "dimensions": [round(maximum[index] - minimum[index], 4) for index in range(3)],
    }


def import_variant(name: str, roll_degrees: float):
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(FBX),
        "destination_path": DEST + "/" + name,
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
        # Unreal's Python constructor is (roll, pitch, yaw), not (pitch, yaw, roll).
        "import_rotation": unreal.Rotator(roll_degrees, 0.0, 0.0),
        "build_nanite": False,
    })
    factory = unreal.FbxFactory()
    factory.set_editor_property("asset_import_task", task)
    task.factory = factory
    task.options = options
    ASSET_TOOLS.import_asset_tasks([task])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    paths = [str(path) for path in task.get_editor_property("imported_object_paths")]
    if len(paths) != 1:
        fail("{} did not yield exactly one static mesh: {}".format(name, paths))
    mesh = unreal.load_asset(paths[0])
    if not isinstance(mesh, unreal.StaticMesh):
        fail(name + " did not resolve a static mesh")
    data = mesh.get_editor_property("asset_import_data")
    recorded = data.get_editor_property("import_rotation")
    return {
        "asset": mesh.get_path_name(),
        "triangles": int(mesh.get_num_triangles(0)),
        "bounds_cm": bounds_cm(mesh),
        "recorded_import_rotation": {
            "pitch": round(float(recorded.pitch), 4),
            "yaw": round(float(recorded.yaw), 4),
            "roll": round(float(recorded.roll), 4),
        },
    }


def main():
    try:
        if not MANIFEST.is_file() or not FBX.is_file():
            fail("source handoff is absent")
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if sha256(FBX) != manifest.get("modules", {}).get("S03", {}).get("fbx_sha256"):
            fail("S03 source FBX hash drift")
        if LIBRARY.does_directory_exist(DEST):
            fail("fresh orientation-probe namespace already exists")
        variants = {name: import_variant(name, roll) for name, roll in VARIANTS.items()}
        target = [716.0, 630.0, 1070.0]
        passing = [
            name for name, row in variants.items()
            if row["bounds_cm"]["dimensions"] == target
        ]
        result = {
            "$schema": "lineboss/onefactory/press/openframe-orientation-probe/v2",
            "generated_utc": utc_now(),
            "source_fbx": str(FBX),
            "source_fbx_sha256": sha256(FBX),
            "expected_source_dimensions_cm": target,
            "map_opened": False,
            "map_saved": False,
            "source_assets_mutated": False,
            "content_writes": [DEST],
            "variants": variants,
            "dimension_passing_variants": passing,
        }
        AUDIT.parent.mkdir(parents=True, exist_ok=True)
        AUDIT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        unreal.log("OPENFRAME_ORIENTATION_PROBE_V002_PASS=" + str(AUDIT))
    finally:
        unreal.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main()
