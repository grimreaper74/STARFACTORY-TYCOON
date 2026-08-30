"""Validate an already-imported S02 runtime pair and write its promotion receipt.

Used only after an import completed but its final semantic check needed
correction. This is read-only with respect to Content: it never imports,
overwrites, opens a level, or saves an asset.
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
STATIC_PATH = DESTINATION + "/SM_CA_S02DeepDraw_Static_v001.SM_CA_S02DeepDraw_Static_v001"
RAM_PATH = DESTINATION + "/SM_CA_S02DeepDraw_Ram_v001.SM_CA_S02DeepDraw_Ram_v001"
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
    raise RuntimeError("S02 deep-draw runtime validation failed: {}".format(message))


def inspect_mesh(object_path):
    mesh = unreal.load_asset(object_path)
    if mesh is None or not isinstance(mesh, unreal.StaticMesh):
        fail("asset is not a StaticMesh: {}".format(object_path))
    bounds = mesh.get_bounding_box()
    size = bounds.max - bounds.min
    return {
        "mesh_object_path": object_path,
        "dimensions_cm": [round(size.x, 2), round(size.y, 2), round(size.z, 2)],
        "material_slots": [str(slot.material_slot_name) for slot in mesh.static_materials],
    }


for path in (SOURCE_STATIC, SOURCE_RAM):
    if not os.path.isfile(path):
        fail("source FBX is missing: {}".format(path))
if not unreal.EditorAssetLibrary.does_directory_exist(DESTINATION):
    fail("runtime destination is missing: {}".format(DESTINATION))

static_result = inspect_mesh(STATIC_PATH)
ram_result = inspect_mesh(RAM_PATH)

static_dimensions = static_result["dimensions_cm"]
if not (500.0 <= static_dimensions[0] <= 900.0
        and 500.0 <= static_dimensions[1] <= 900.0
        and 650.0 <= static_dimensions[2] <= 950.0):
    fail("unexpected static-shell dimensions in cm: {}".format(static_dimensions))
if not all(value > 1.0 for value in ram_result["dimensions_cm"]):
    fail("ram module has empty or degenerate dimensions in cm: {}".format(
        ram_result["dimensions_cm"]))

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
if "M_CA_DarkSteel" not in ram_result["material_slots"]:
    fail("ram module lost its tooling-steel semantic slot: {}".format(
        ram_result["material_slots"]))

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
