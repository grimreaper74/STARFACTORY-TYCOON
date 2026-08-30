"""Asset-only native Unreal import for the coil-free Meshy infeed feeder.

The FBX is a derivative of the user-supplied textured Meshy source. Its
embedded coil was removed in Blender; project-owned coils stay separate level
actors. This script never loads or saves a map.
"""

import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = PROJECT / "SourceAssets" / "Candidate" / "PressShop" / "MeshyCoilFeederNoCoil_v001" / "SM_LB_PS_InfeedCoilFeeder_NoCoil_v001.fbx"
ROOT = "/Game/LineBoss/Candidates/PressShop/MeshyCoilFeederNoCoil_v001"
ASSET_NAME = "SM_LB_PS_InfeedCoilFeeder_NoCoil_v001"
TARGET = ROOT + "/" + ASSET_NAME
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_meshy_coilfeeder_import_v001.json"


def fail(message):
    raise RuntimeError("COILFEEDER_IMPORT_FAIL: " + message)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


if not SOURCE.is_file():
    fail("missing derived FBX: " + str(SOURCE))

mesh = unreal.load_asset(TARGET) if unreal.EditorAssetLibrary.does_asset_exist(TARGET) else None
if mesh is None:
    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_as_skeletal", False)
    options.set_editor_property("import_materials", True)
    options.set_editor_property("import_textures", True)
    options.static_mesh_import_data.set_editor_property("combine_meshes", True)
    options.static_mesh_import_data.set_editor_property("auto_generate_collision", False)
    options.static_mesh_import_data.set_editor_property("import_uniform_scale", 1.0)
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(SOURCE),
        "destination_path": ROOT,
        "destination_name": ASSET_NAME,
        "automated": True,
        "replace_existing": False,
        "save": True,
        "options": options,
    })
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported = list(task.get_editor_property("imported_object_paths") or [])
    if TARGET not in imported:
        fail("expected static mesh import at %s, got %s" % (TARGET, imported))
    mesh = unreal.load_asset(TARGET)

if not isinstance(mesh, unreal.StaticMesh):
    fail("static mesh not available after import")
bounds = mesh.get_bounding_box()
dims = [bounds.max.x - bounds.min.x, bounds.max.y - bounds.min.y, bounds.max.z - bounds.min.z]
expected_sorted = sorted((1638.401, 790.401, 800.0))
if any(abs(actual - expected) > 4.0 for actual, expected in zip(sorted(dims), expected_sorted)):
    fail("unexpected dimensions in cm: %s" % dims)
triangles = int(mesh.get_num_triangles(0))
if triangles <= 0 or triangles > 14181:
    fail("unexpected LOD0 triangle count: %s" % triangles)
slots = list(mesh.get_editor_property("static_materials"))
if len(slots) != 1 or slots[0].material_interface is None:
    fail("textured source did not provide one usable material slot")
unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)

assets = unreal.EditorAssetLibrary.list_assets(ROOT, recursive=True, include_folder=False)
receipt = {
    "status": "PASS__NATIVE_UNREAL_IMPORT_OF_COIL_FREE_MESHY_FEEDER",
    "map_loaded": False,
    "map_saved": False,
    "source_fbx": str(SOURCE),
    "source_fbx_sha256": sha256(SOURCE),
    "mesh": mesh.get_path_name(),
    "dimensions_cm": [round(value, 3) for value in dims],
    "triangles_lod0": triangles,
    "material_slots": [str(slot.material_slot_name) for slot in slots],
    "material_assets": [slot.material_interface.get_path_name() for slot in slots],
    "generated_assets": sorted(assets),
    "coil_policy": "This feeder has no embedded coil. It must be paired only with existing approved wrapped/bare coil actors in the candidate map.",
    "collision": "none authored; automatic collision deliberately disabled",
    "lods": "LOD0 only; no optimization or in-engine performance claim",
}
RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
print(json.dumps(receipt, indent=2))
