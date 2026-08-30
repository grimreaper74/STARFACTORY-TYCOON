"""Native Unreal candidate import for the five cleaned square Meshy presses.

Asset-only: this never loads, edits, or saves a map.  It imports only under
/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001.
"""
import hashlib
import json
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = PROJECT / "SourceAssets" / "Candidate" / "PressShop" / "SquareMeshyPressTrain_v001"
ROOT = "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001"
MATERIAL_ROOT = ROOT + "/Materials"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "square_meshy_press_train_import_v001.json"
SPECS = {
    "S02_DrawForm": ((1403.51, 640.93, 838.0), 15240),
    "S03_Trim": ((1036.12, 1325.57, 838.0), 15253),
    "S04_Pierce": ((801.57, 788.61, 838.0), 14064),
    "S05_FlangeHem": ((1060.35, 1204.71, 838.0), 14018),
    "S06_VisionOutfeed": ((736.37, 1066.67, 538.0), 15315),
}
PALETTE = {
    "M_LB_PS_CairnwellGreen": ((31 / 255, 75 / 255, 68 / 255), 0.25, 0.43),
    "M_LB_PS_FoundryCharcoal": ((32 / 255, 36 / 255, 40 / 255), 0.50, 0.34),
    "M_LB_PS_SteelGrey": ((112 / 255, 119 / 255, 124 / 255), 0.72, 0.30),
    "M_LB_PS_WarmWhite": ((243 / 255, 241 / 255, 233 / 255), 0.15, 0.38),
    "M_LB_PS_SafetyYellow": ((242 / 255, 195 / 255, 0 / 255), 0.28, 0.36),
    "M_LB_PS_StatusRed": ((199 / 255, 53 / 255, 44 / 255), 0.18, 0.38),
}
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
MEL = unreal.MaterialEditingLibrary


def fail(message):
    raise RuntimeError("SQUARE_MESHY_PRESS_TRAIN_IMPORT_FAIL: " + message)


def digest(path):
    value = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def material(name, rgb, metallic, roughness):
    path = MATERIAL_ROOT + "/" + name
    asset = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if asset is None:
        asset = TOOLS.create_asset(name, MATERIAL_ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if not isinstance(asset, unreal.Material):
        fail("material creation failed for " + name)
    if hasattr(MEL, "delete_all_material_expressions"):
        MEL.delete_all_material_expressions(asset)
    base = MEL.create_material_expression(asset, unreal.MaterialExpressionConstant3Vector, -400, -100)
    base.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    metallic_node = MEL.create_material_expression(asset, unreal.MaterialExpressionConstant, -400, 50)
    metallic_node.set_editor_property("r", metallic)
    roughness_node = MEL.create_material_expression(asset, unreal.MaterialExpressionConstant, -400, 180)
    roughness_node.set_editor_property("r", roughness)
    MEL.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(metallic_node, "", unreal.MaterialProperty.MP_METALLIC)
    MEL.connect_material_property(roughness_node, "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(asset)
    unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
    return asset


def asset_path(name):
    return ROOT + "/SM_LB_PS_%s_MeshyClean_v001" % name


def import_one(station, expected_dims, source_triangles, native_materials):
    fbx = SOURCE / "Cleaned" / ("SM_LB_PS_%s_MeshyClean_v001.fbx" % station)
    if not fbx.is_file():
        fail("missing FBX " + str(fbx))
    target = asset_path(station)
    mesh = unreal.load_asset(target) if unreal.EditorAssetLibrary.does_asset_exist(target) else None
    if mesh is None:
        options = unreal.FbxImportUI()
        options.set_editor_property("import_mesh", True)
        options.set_editor_property("import_materials", False)
        options.set_editor_property("import_textures", False)
        options.set_editor_property("import_as_skeletal", False)
        options.static_mesh_import_data.set_editor_property("combine_meshes", True)
        options.static_mesh_import_data.set_editor_property("auto_generate_collision", False)
        options.static_mesh_import_data.set_editor_property("import_uniform_scale", 1.0)
        task = unreal.AssetImportTask()
        task.set_editor_properties({"filename": str(fbx), "destination_path": ROOT, "destination_name": "SM_LB_PS_%s_MeshyClean_v001" % station, "automated": True, "replace_existing": False, "save": True, "options": options})
        TOOLS.import_asset_tasks([task])
        paths = list(task.get_editor_property("imported_object_paths") or [])
        if len(paths) != 1:
            fail("%s import produced %s" % (station, paths))
        mesh = unreal.load_asset(paths[0])
    if not isinstance(mesh, unreal.StaticMesh):
        fail(station + " did not resolve to a static mesh")
    bounds = mesh.get_bounding_box()
    dimensions = (bounds.max.x - bounds.min.x, bounds.max.y - bounds.min.y, bounds.max.z - bounds.min.z)
    if any(abs(actual - expected) > 4.0 for actual, expected in zip(sorted(dimensions), sorted(expected_dims))):
        fail("%s dimensions %s do not match expected size %s cm" % (station, dimensions, expected_dims))
    slots = list(mesh.get_editor_property("static_materials"))
    slot_names = [str(slot.material_slot_name) for slot in slots]
    if set(slot_names) != set(PALETTE):
        fail("%s slot names %s do not exactly match approved palette" % (station, slot_names))
    for index, slot_name in enumerate(slot_names):
        mesh.set_material(index, native_materials[slot_name])
    triangles = int(mesh.get_num_triangles(0))
    if triangles <= 0 or triangles > source_triangles:
        fail("%s Unreal LOD0 triangles %s invalid vs FBX %s" % (station, triangles, source_triangles))
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
    return {"path": mesh.get_path_name(), "source_fbx": str(fbx), "source_fbx_sha256": digest(fbx), "source_triangles": source_triangles, "unreal_triangles_lod0": triangles, "bounds_cm": [round(value, 3) for value in dimensions], "material_slots": slot_names}


native_materials = {name: material(name, *definition) for name, definition in PALETTE.items()}
imports = {station: import_one(station, *spec, native_materials) for station, spec in SPECS.items()}
receipt = {
    "status": "PASS__CANDIDATE_ASSETS_IMPORTED_WITH_NATIVE_UNREAL_MATERIALS",
    "map_loaded": False,
    "map_saved": False,
    "destination": ROOT,
    "assets": imports,
    "materials": {name: asset.get_path_name() for name, asset in native_materials.items()},
    "collision": "not authored; automatic collision explicitly disabled",
    "lods": "LOD0 only; no optimization claim",
    "coils": "none included in the imported machine meshes; use the already-approved project coil actors separately",
    "next_gate": "build a new isolated review map and take in-engine management-camera screenshots before any protected-map placement."
}
RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.EditorAssetLibrary.save_directory(ROOT, only_if_is_dirty=False, recursive=True)
unreal.log("LINE_BOSS_SQUARE_MESHY_PRESS_TRAIN_IMPORT=" + json.dumps(receipt, sort_keys=True))
