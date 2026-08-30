"""Guarded no-map promotion of Claude's verified S02 RuntimePrep v002 FBXs.

This does not modify or overwrite the provisional v001 import. The v002 source
is imported into its own owned namespace, one combined StaticMesh per export,
with source material slots preserved and FBX materials/textures disabled. A
receipt records exact bounds, slot order, and source hashes for runtime code.
"""

import hashlib
import io
import json
import os

import unreal


PROJECT_ROOT = r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8"
SOURCE_DIR = PROJECT_ROOT + "/ArtSource/Claude_S02_DeepDraw_RuntimePrep_v002"
DESTINATION = (
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
    "DetailedPresentation_v001/S02DeepDraw_v002"
)
RECEIPT = (
    PROJECT_ROOT
    + "/Saved/Audits/OneFactory/Press/S02DeepDrawRuntimePrep_v002/import_receipt.json"
)

EXPORTS = (
    {
        "key": "Static",
        "fbx": "CA_S02_DeepDraw_Static_LOD0.fbx",
        "asset_name": "SM_CA_S02DeepDraw_Static_LOD0_v002",
        "dimensions_cm": (657.0, 663.09, 815.06),
        "material_slots": (
            "M_CA_MainGreen", "M_CA_Concrete", "M_CA_DarkSteel",
            "M_CA_CleanSteel", "M_CA_CharcoalGrey", "M_CA_SafetyYellow",
            "M_CA_ScreenDark", "M_CA_LampGreen", "M_CA_LampAmber",
            "M_CA_LampRed",
        ),
    },
    {
        "key": "Ram",
        "fbx": "CA_S02_DeepDraw_Ram_LOD0.fbx",
        "asset_name": "SM_CA_S02DeepDraw_Ram_LOD0_v002",
        "dimensions_cm": (222.0, 180.0, 188.0),
        "material_slots": ("M_CA_DarkSteel",),
    },
    {
        "key": "Blankholder",
        "fbx": "CA_S02_DeepDraw_Blankholder_LOD0.fbx",
        "asset_name": "SM_CA_S02DeepDraw_Blankholder_LOD0_v002",
        "dimensions_cm": (190.0, 155.0, 12.0),
        "material_slots": ("M_CA_CleanSteel",),
    },
    {
        "key": "Bolster",
        "fbx": "CA_S02_DeepDraw_Bolster_LOD0.fbx",
        "asset_name": "SM_CA_S02DeepDraw_Bolster_LOD0_v002",
        "dimensions_cm": (210.0, 200.0, 36.0),
        "material_slots": ("M_CA_CleanSteel",),
    },
    {
        "key": "Flywheel",
        "fbx": "CA_S02_DeepDraw_Flywheel_LOD0.fbx",
        "asset_name": "SM_CA_S02DeepDraw_Flywheel_LOD0_v002",
        "dimensions_cm": (194.0, 43.0, 194.0),
        "material_slots": ("M_CA_DarkSteel",),
    },
    {
        "key": "SafetyGate",
        "fbx": "CA_S02_DeepDraw_SafetyGate_LOD0.fbx",
        "asset_name": "SM_CA_S02DeepDraw_SafetyGate_LOD0_v002",
        "dimensions_cm": (92.0, 11.5, 160.0),
        "material_slots": ("M_CA_SafetyYellow",),
    },
)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def fail(message):
    raise RuntimeError("S02 RuntimePrep v002 import failed: {}".format(message))


def import_mesh(spec):
    source_fbx = SOURCE_DIR + "/" + spec["fbx"]
    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("import_as_skeletal", False)
    options.static_mesh_import_data.set_editor_property("combine_meshes", True)
    options.static_mesh_import_data.set_editor_property("auto_generate_collision", False)
    options.static_mesh_import_data.set_editor_property("import_uniform_scale", 1.0)

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", source_fbx)
    task.set_editor_property("destination_path", DESTINATION)
    task.set_editor_property("destination_name", spec["asset_name"])
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", False)
    task.set_editor_property("save", True)
    task.set_editor_property("options", options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    imported_paths = list(task.get_editor_property("imported_object_paths") or [])
    if len(imported_paths) != 1:
        fail("expected one combined StaticMesh for {} but got {}: {}".format(
            spec["key"], len(imported_paths), imported_paths))
    mesh = unreal.load_asset(imported_paths[0])
    if mesh is None or not isinstance(mesh, unreal.StaticMesh):
        fail("{} did not resolve to a StaticMesh".format(spec["key"]))

    bounds = mesh.get_bounding_box()
    size = bounds.max - bounds.min
    dimensions = (round(size.x, 2), round(size.y, 2), round(size.z, 2))
    expected_dimensions = spec["dimensions_cm"]
    if any(abs(actual - expected) > 3.0
           for actual, expected in zip(dimensions, expected_dimensions)):
        fail("{} bounds differ from RuntimePrep receipt: got {}, expected {}".format(
            spec["key"], dimensions, expected_dimensions))

    slots = tuple(str(slot.material_slot_name) for slot in mesh.static_materials)
    if slots != spec["material_slots"]:
        fail("{} semantic material slots differ: got {}, expected {}".format(
            spec["key"], slots, spec["material_slots"]))

    return {
        "source_fbx": source_fbx,
        "source_fbx_sha256": sha256(source_fbx),
        "mesh_object_path": imported_paths[0],
        "dimensions_cm": dimensions,
        "material_slots": slots,
        "combined_meshes": True,
    }


for spec in EXPORTS:
    source_path = SOURCE_DIR + "/" + spec["fbx"]
    if not os.path.isfile(source_path):
        fail("RuntimePrep source is missing: {}".format(source_path))
if unreal.EditorAssetLibrary.does_directory_exist(DESTINATION):
    fail("destination already exists; overwrite is forbidden: {}".format(DESTINATION))

results = {}
for spec in EXPORTS:
    results[spec["key"]] = import_mesh(spec)

stats_path = SOURCE_DIR + "/runtime_prep_stats.json"
receipt = {
    "schema": "lineboss/onefactory/press/s02-deepdraw-runtimeprep-v002-import/v1",
    "status": "PASS__RUNTIMEPREP_V002_IMPORTS_AT_RECEIPTED_UNREAL_SCALE",
    "destination": DESTINATION,
    "modules": results,
    "runtime_prep_stats": stats_path,
    "runtime_prep_stats_sha256": sha256(stats_path),
    "imported_materials": False,
    "imported_textures": False,
    "auto_generated_collision": False,
    "map_loaded": False,
    "map_saved": False,
}
os.makedirs(os.path.dirname(RECEIPT), exist_ok=True)
with io.open(RECEIPT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")

unreal.log("LINE_BOSS_S02_RUNTIMEPREP_V002_IMPORT=" + json.dumps(receipt, sort_keys=True))
