"""Guarded, non-map import check for the hand-authored S02 deep-draw source.

This is deliberately a preflight only: it imports one combined static mesh to
the native OneFactory press namespace, verifies the FBX units/axes/material
slots in a fresh Unreal process, writes a receipt, and never loads or saves a
level.  It refuses to overwrite an existing destination.
"""

import hashlib
import io
import json
import os

import unreal


PROJECT_ROOT = r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8"
SOURCE_FBX = PROJECT_ROOT + "/ArtSource/Claude_S02_DeepDraw_v001/CA_S02_DeepDraw_v001.fbx"
DESTINATION = (
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
    "DetailedPresentation_v001/S02DeepDrawPreflight_v001"
)
DESTINATION_NAME = "SM_CA_S02DeepDraw_Preflight_v001"
EXPECTED_SLOT_NAMES = {
    "M_CA_MainGreen",
    "M_CA_DarkSteel",
    "M_CA_CleanSteel",
    "M_CA_SafetyYellow",
}
RECEIPT = (
    PROJECT_ROOT
    + "/Saved/Audits/OneFactory/Press/S02DeepDrawPreflight_v001/import_receipt.json"
)


def source_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def fail(message):
    raise RuntimeError("S02 deep-draw preflight failed: {}".format(message))


if not os.path.isfile(SOURCE_FBX):
    fail("source FBX is missing: {}".format(SOURCE_FBX))
if unreal.EditorAssetLibrary.does_directory_exist(DESTINATION):
    fail("destination already exists; overwrite is forbidden: {}".format(DESTINATION))

options = unreal.FbxImportUI()
options.set_editor_property("import_mesh", True)
options.set_editor_property("import_materials", False)
options.set_editor_property("import_textures", False)
options.set_editor_property("import_as_skeletal", False)
options.static_mesh_import_data.set_editor_property("combine_meshes", True)
options.static_mesh_import_data.set_editor_property("import_uniform_scale", 1.0)

task = unreal.AssetImportTask()
task.set_editor_property("filename", SOURCE_FBX)
task.set_editor_property("destination_path", DESTINATION)
task.set_editor_property("destination_name", DESTINATION_NAME)
task.set_editor_property("automated", True)
task.set_editor_property("replace_existing", False)
task.set_editor_property("save", True)
task.set_editor_property("options", options)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

imported_paths = list(task.get_editor_property("imported_object_paths") or [])
if len(imported_paths) != 1:
    fail("expected exactly one combined imported mesh, got {}: {}".format(
        len(imported_paths), imported_paths))

object_path = imported_paths[0]
mesh = unreal.load_asset(object_path)
if mesh is None or not isinstance(mesh, unreal.StaticMesh):
    fail("import did not resolve one StaticMesh: {}".format(object_path))

bounds = mesh.get_bounding_box()
size = bounds.max - bounds.min
dimensions_cm = [round(size.x, 2), round(size.y, 2), round(size.z, 2)]

# The source README records a 6.4 m x 6.6 m x ~8.0 m cell envelope.  These
# intentionally broad bounds catch the two dangerous cases: metre values being
# treated as centimetres (tiny) or centimetres being multiplied again (huge).
if not (500.0 <= size.x <= 900.0 and 500.0 <= size.y <= 900.0
        and 650.0 <= size.z <= 950.0):
    fail("unexpected imported bounds in cm: {}".format(dimensions_cm))

slot_names = [str(slot.material_slot_name) for slot in mesh.static_materials]
missing_slots = sorted(EXPECTED_SLOT_NAMES.difference(slot_names))
if missing_slots:
    fail("semantic material slots were not preserved: {}; saw {}".format(
        missing_slots, slot_names))

receipt = {
    "schema": "lineboss/onefactory/press/s02-deepdraw-preflight/v1",
    "status": "PASS__SOURCE_FBX_IMPORTS_AT_EXPECTED_UNREAL_SCALE",
    "source_fbx": SOURCE_FBX,
    "source_sha256": source_sha256(SOURCE_FBX),
    "destination": DESTINATION,
    "mesh_object_path": object_path,
    "dimensions_cm": dimensions_cm,
    "material_slots": slot_names,
    "combined_meshes": True,
    "imported_materials": False,
    "imported_textures": False,
    "map_loaded": False,
    "map_saved": False,
}
os.makedirs(os.path.dirname(RECEIPT), exist_ok=True)
with io.open(RECEIPT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")

unreal.log("LINE_BOSS_S02_DEEPDRAW_PREFLIGHT=" + json.dumps(receipt, sort_keys=True))
