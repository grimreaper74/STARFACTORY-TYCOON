"""Import only the prepared low-poly hero press into a candidate Content folder.

No level is loaded, changed or saved.  This deliberately establishes an Unreal-native
material and import receipt before any visual staging decision is made.
"""
import hashlib
import json
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = PROJECT / "SourceAssets" / "Candidate" / "PressShop" / "HeroPressCell_MeshyLowPoly_v001"
FBX = SOURCE / "Runtime" / "SM_LB_PS_HeroPressCell_MeshyLP_v001.fbx"
TEXTURES = {
    "BaseColor": SOURCE / "Textures" / "T_LB_PS_HeroPressCell_MeshyLP_BaseColor_v001.png",
    "MetallicRoughness": SOURCE / "Textures" / "T_LB_PS_HeroPressCell_MeshyLP_MetallicRoughness_v001.png",
    "Normal": SOURCE / "Textures" / "T_LB_PS_HeroPressCell_MeshyLP_Normal_v001.png",
}
DESTINATION = "/Game/LineBoss/Candidates/PressShop/HeroPressCell_MeshyLowPoly_v001"
TEXTURE_DESTINATION = DESTINATION + "/Textures"
MATERIAL_DESTINATION = DESTINATION + "/Materials"
MESH_NAME = "SM_LB_PS_HeroPressCell_MeshyLP_v001"
MASTER_NAME = "M_LB_PS_HeroPressCell_MeshyLP_v001"
INSTANCE_NAME = "MI_LB_PS_HeroPressCell_MeshyLP_v001"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "hero_press_cell_meshylp_unreal_import_v001.json"
EXPECTED_BOUNDS_CM = (1914.018, 618.691, 800.0)

ASSET_TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
MEL = unreal.MaterialEditingLibrary


def fail(message):
    raise RuntimeError("HERO_PRESS_CELL_IMPORT_FAIL: " + message)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def object_path(folder, name):
    return folder + "/" + name


def ensure_file(path):
    if not path.is_file():
        fail("missing source '{}'".format(path))


def import_texture(key, path):
    asset_name = path.stem
    asset_path = object_path(TEXTURE_DESTINATION, asset_name)
    texture = unreal.load_asset(asset_path) if unreal.EditorAssetLibrary.does_asset_exist(asset_path) else None
    if texture is None:
        task = unreal.AssetImportTask()
        task.set_editor_property("filename", str(path))
        task.set_editor_property("destination_path", TEXTURE_DESTINATION)
        task.set_editor_property("destination_name", asset_name)
        task.set_editor_property("automated", True)
        task.set_editor_property("replace_existing", False)
        task.set_editor_property("save", True)
        ASSET_TOOLS.import_asset_tasks([task])
        imported = list(task.get_editor_property("imported_object_paths") or [])
        if len(imported) != 1:
            fail("expected one {} texture import, got {}".format(key, imported))
        texture = unreal.load_asset(imported[0])
    if not isinstance(texture, unreal.Texture):
        fail("{} did not resolve to a texture".format(key))
    if key == "BaseColor":
        texture.set_editor_property("srgb", True)
    elif key == "Normal":
        texture.set_editor_property("srgb", False)
        texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
        texture.set_editor_property("flip_green_channel", True)
    else:
        texture.set_editor_property("srgb", False)
        texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
    unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)
    return texture


def import_mesh():
    expected_path = object_path(DESTINATION, MESH_NAME)
    mesh = unreal.load_asset(expected_path) if unreal.EditorAssetLibrary.does_asset_exist(expected_path) else None
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
        task.set_editor_property("filename", str(FBX))
        task.set_editor_property("destination_path", DESTINATION)
        task.set_editor_property("destination_name", MESH_NAME)
        task.set_editor_property("automated", True)
        task.set_editor_property("replace_existing", False)
        task.set_editor_property("save", True)
        task.set_editor_property("options", options)
        ASSET_TOOLS.import_asset_tasks([task])
        imported = list(task.get_editor_property("imported_object_paths") or [])
        if len(imported) != 1:
            fail("expected one static mesh import, got {}".format(imported))
        mesh = unreal.load_asset(imported[0])
    if not isinstance(mesh, unreal.StaticMesh):
        fail("FBX did not resolve to a static mesh")
    bounds = mesh.get_bounding_box()
    actual = (bounds.max.x - bounds.min.x, bounds.max.y - bounds.min.y, bounds.max.z - bounds.min.z)
    if any(abs(got - expected) > 3.0 for got, expected in zip(actual, EXPECTED_BOUNDS_CM)):
        fail("cm bounds {} do not match expected {}".format(actual, EXPECTED_BOUNDS_CM))
    return mesh, tuple(round(value, 3) for value in actual)


def expression(material, klass, x, y):
    return MEL.create_material_expression(material, klass, x, y)


def texture_sample(material, parameter, texture, sampler_type, x, y, texcoord):
    sample = expression(material, unreal.MaterialExpressionTextureSampleParameter2D, x, y)
    sample.set_editor_properties({
        "parameter_name": parameter,
        "texture": texture,
        "sampler_type": sampler_type,
    })
    MEL.connect_material_expressions(texcoord, "", sample, "UVs")
    return sample


def component_mask(material, source, channel, x, y):
    mask = expression(material, unreal.MaterialExpressionComponentMask, x, y)
    mask.set_editor_property(channel.lower(), True)
    MEL.connect_material_expressions(source, "RGB", mask, "")
    return mask


def build_material(textures):
    master_path = object_path(MATERIAL_DESTINATION, MASTER_NAME)
    master = unreal.load_asset(master_path) if unreal.EditorAssetLibrary.does_asset_exist(master_path) else None
    if master is None:
        master = ASSET_TOOLS.create_asset(MASTER_NAME, MATERIAL_DESTINATION, unreal.Material, unreal.MaterialFactoryNew())
    if not isinstance(master, unreal.Material):
        fail("could not make native material")
    if hasattr(MEL, "delete_all_material_expressions"):
        MEL.delete_all_material_expressions(master)
    master.set_editor_property("two_sided", False)
    uv = expression(master, unreal.MaterialExpressionTextureCoordinate, -1100, 0)
    uv.set_editor_property("coordinate_index", 0)
    base = texture_sample(master, "BaseColorMap", textures["BaseColor"], unreal.MaterialSamplerType.SAMPLERTYPE_COLOR, -850, -180, uv)
    normal = texture_sample(master, "NormalMap", textures["Normal"], unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL, -850, 60, uv)
    metalrough = texture_sample(master, "MetallicRoughnessMap", textures["MetallicRoughness"], unreal.MaterialSamplerType.SAMPLERTYPE_MASKS, -850, 310, uv)
    MEL.connect_material_property(base, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(normal, "RGB", unreal.MaterialProperty.MP_NORMAL)
    metallic = component_mask(master, metalrough, "B", -590, 290)
    MEL.connect_material_property(metallic, "", unreal.MaterialProperty.MP_METALLIC)
    roughness = component_mask(master, metalrough, "G", -590, 390)
    roughness_multiplier = expression(master, unreal.MaterialExpressionScalarParameter, -600, 500)
    roughness_multiplier.set_editor_properties({"parameter_name": "RoughnessMultiplier", "default_value": 1.30})
    adjusted_roughness = expression(master, unreal.MaterialExpressionMultiply, -360, 400)
    MEL.connect_material_expressions(roughness, "", adjusted_roughness, "A")
    MEL.connect_material_expressions(roughness_multiplier, "", adjusted_roughness, "B")
    MEL.connect_material_property(adjusted_roughness, "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(master)
    unreal.EditorAssetLibrary.save_loaded_asset(master, only_if_is_dirty=False)

    instance_path = object_path(MATERIAL_DESTINATION, INSTANCE_NAME)
    instance = unreal.load_asset(instance_path) if unreal.EditorAssetLibrary.does_asset_exist(instance_path) else None
    if instance is None:
        instance = ASSET_TOOLS.create_asset(INSTANCE_NAME, MATERIAL_DESTINATION,
                                            unreal.MaterialInstanceConstant,
                                            unreal.MaterialInstanceConstantFactoryNew())
    instance.set_editor_property("parent", master)
    MEL.set_material_instance_texture_parameter_value(instance, "BaseColorMap", textures["BaseColor"])
    MEL.set_material_instance_texture_parameter_value(instance, "NormalMap", textures["Normal"])
    MEL.set_material_instance_texture_parameter_value(instance, "MetallicRoughnessMap", textures["MetallicRoughness"])
    MEL.set_material_instance_scalar_parameter_value(instance, "RoughnessMultiplier", 1.30)
    unreal.EditorAssetLibrary.save_loaded_asset(instance, only_if_is_dirty=False)
    return master, instance


for path in [FBX] + list(TEXTURES.values()):
    ensure_file(path)
texture_assets = {key: import_texture(key, path) for key, path in TEXTURES.items()}
mesh, bounds_cm = import_mesh()
master, instance = build_material(texture_assets)
mesh.set_material(0, instance)
unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)

triangles = None
try:
    triangles = int(mesh.get_num_triangles(0))
except Exception:
    pass
if triangles is not None and triangles != 3917:
    fail("imported LOD0 triangle count {} differs from 3,917 source triangles".format(triangles))

receipt = {
    "status": "PASS__CANDIDATE_IMPORTED_WITH_NATIVE_PBR_MATERIAL__NOT_PLACED",
    "map_loaded": False,
    "map_saved": False,
    "source": {"fbx": str(FBX), "fbx_sha256": sha256(FBX)},
    "static_mesh": {"path": mesh.get_path_name(), "bounds_cm": bounds_cm, "triangles_lod0": triangles},
    "textures": {key: {"path": texture.get_path_name(), "source_sha256": sha256(TEXTURES[key])}
                 for key, texture in texture_assets.items()},
    "native_material": {"master": master.get_path_name(), "instance": instance.get_path_name(),
                        "roughness_multiplier": 1.30, "normal_green_flipped": True},
    "collision": "not authored; import auto-generation explicitly disabled",
    "next_gate": "Place only into a dedicated Press Shop review child after a saved-map baseline is confirmed.",
}
RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.EditorAssetLibrary.save_directory(DESTINATION, only_if_is_dirty=False, recursive=True)
unreal.log("LINE_BOSS_HERO_PRESS_CELL_IMPORT=" + json.dumps(receipt, sort_keys=True))
