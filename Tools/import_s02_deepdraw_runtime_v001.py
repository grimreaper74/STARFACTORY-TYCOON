"""Guarded no-map import of the derived S02 static shell and ram module.

This promotion lane is deliberately non-destructive: both source derivatives
must exist, the final Unreal namespace must be empty, and no level is loaded or
saved. A receipt records the exact resulting asset paths, dimensions and source
hashes for the C++ provenance closure.
"""

import hashlib
import io
import json
import os

import unreal


PROJECT_ROOT = r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8"
SOURCE_STATIC = PROJECT_ROOT + "/ArtSource/Codex_S02_DeepDraw_Static_v001/CA_S02_DeepDraw_Static_v001.fbx"
SOURCE_RAM = PROJECT_ROOT + "/ArtSource/Codex_S02_DeepDraw_Ram_v001/CA_S02_DeepDraw_Ram_v001.fbx"
DESTINATION = (
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
    "DetailedPresentation_v001/S02DeepDraw_v001"
)
STATIC_NAME = "SM_CA_S02DeepDraw_Static_v001"
RAM_NAME = "SM_CA_S02DeepDraw_Ram_v001"
RECEIPT = (
    PROJECT_ROOT
    + "/Saved/Audits/OneFactory/Press/S02DeepDrawRuntime_v001/import_receipt.json"
)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def fail(message):
    raise RuntimeError("S02 deep-draw runtime import failed: {}".format(message))


def import_mesh(source_fbx, destination_name):
    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("import_as_skeletal", False)
    options.static_mesh_import_data.set_editor_property("combine_meshes", True)
    options.static_mesh_import_data.set_editor_property("import_uniform_scale", 1.0)

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", source_fbx)
    task.set_editor_property("destination_path", DESTINATION)
    task.set_editor_property("destination_name", destination_name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", False)
    task.set_editor_property("save", True)
    task.set_editor_property("options", options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    imported_paths = list(task.get_editor_property("imported_object_paths") or [])
    if len(imported_paths) != 1:
        fail("expected one combined mesh for {}; got {}: {}".format(
            destination_name, len(imported_paths), imported_paths))

    mesh = unreal.load_asset(imported_paths[0])
    if mesh is None or not isinstance(mesh, unreal.StaticMesh):
        fail("import did not resolve one StaticMesh: {}".format(imported_paths[0]))

    bounds = mesh.get_bounding_box()
    size = bounds.max - bounds.min
    dimensions = [round(size.x, 2), round(size.y, 2), round(size.z, 2)]
    slot_names = [str(slot.material_slot_name) for slot in mesh.static_materials]
    return {
        "mesh_object_path": imported_paths[0],
        "dimensions_cm": dimensions,
        "material_slots": slot_names,
    }


for path in (SOURCE_STATIC, SOURCE_RAM):
    if not os.path.isfile(path):
        fail("source FBX is missing: {}".format(path))
if unreal.EditorAssetLibrary.does_directory_exist(DESTINATION):
    fail("destination already exists; overwrite is forbidden: {}".format(DESTINATION))

static_result = import_mesh(SOURCE_STATIC, STATIC_NAME)
ram_result = import_mesh(SOURCE_RAM, RAM_NAME)

static_dimensions = static_result["dimensions_cm"]
if not (500.0 <= static_dimensions[0] <= 900.0
        and 500.0 <= static_dimensions[1] <= 900.0
        and 650.0 <= static_dimensions[2] <= 950.0):
    fail("unexpected static-shell dimensions in cm: {}".format(static_dimensions))

ram_dimensions = ram_result["dimensions_cm"]
if not all(value > 1.0 for value in ram_dimensions):
    fail("ram module has empty or degenerate dimensions in cm: {}".format(ram_dimensions))

required_static_slots = {
    "M_CA_MainGreen",
    "M_CA_DarkSteel",
    "M_CA_CleanSteel",
    "M_CA_SafetyYellow",
}
missing_static = sorted(required_static_slots.difference(static_result["material_slots"]))
if missing_static:
    fail("static shell lost semantic slots: {}; saw {}".format(
        missing_static, static_result["material_slots"]))

# The RamMover + DieUpper source module intentionally uses the tooling steel
# material only. Requiring structural green here would reject a valid split.
required_ram_slots = {"M_CA_DarkSteel"}
missing_ram = sorted(required_ram_slots.difference(ram_result["material_slots"]))
if missing_ram:
    fail("ram module lost semantic slots: {}; saw {}".format(
        missing_ram, ram_result["material_slots"]))

receipt = {
    "schema": "lineboss/onefactory/press/s02-deepdraw-runtime-import/v1",
    "status": "PASS__DERIVED_STATIC_AND_RAM_IMPORT_AT_EXPECTED_UNREAL_SCALE",
    "destination": DESTINATION,
    "static": static_result,
    "ram": ram_result,
    "source_static_fbx": SOURCE_STATIC,
    "source_static_sha256": sha256(SOURCE_STATIC),
    "source_ram_fbx": SOURCE_RAM,
    "source_ram_sha256": sha256(SOURCE_RAM),
    "combined_meshes": True,
    "imported_materials": False,
    "imported_textures": False,
    "map_loaded": False,
    "map_saved": False,
}
os.makedirs(os.path.dirname(RECEIPT), exist_ok=True)
with io.open(RECEIPT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")

unreal.log("LINE_BOSS_S02_DEEPDRAW_RUNTIME_IMPORT=" + json.dumps(receipt, sort_keys=True))
