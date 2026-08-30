"""Supersede the initial FBX texture import with explicit native PBR wiring.

The source textures are extracted from the same packed Meshy material.  This
does not change any map; it assigns a proper Unreal material to the already
imported coil-free feeder asset.
"""

import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = PROJECT / "SourceAssets" / "Candidate" / "PressShop" / "MeshyCoilFeederNoCoil_v001"
FBX = SOURCE / "SM_LB_PS_InfeedCoilFeeder_NoCoil_v001.fbx"
TEXTURES = {
    "BaseColor": SOURCE / "Textures" / "base_color.png",
    "MetallicRoughness": SOURCE / "Textures" / "metallic_roughness.png",
    "Normal": SOURCE / "Textures" / "normal.png",
}
ROOT = "/Game/LineBoss/Candidates/PressShop/MeshyCoilFeederNoCoil_v001"
TEXTURE_ROOT = ROOT + "/Textures"
MATERIAL_ROOT = ROOT + "/Materials"
MESH_NAME = "SM_LB_PS_InfeedCoilFeeder_NoCoil_v001"
MATERIAL_NAME = "M_LB_PS_InfeedCoilFeeder_Meshy_v001"
INSTANCE_NAME = "MI_LB_PS_InfeedCoilFeeder_Meshy_v001"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_meshy_coilfeeder_import_v002.json"

TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
MEL = unreal.MaterialEditingLibrary


def fail(message):
    raise RuntimeError("COILFEEDER_NATIVE_PBR_IMPORT_FAIL: " + message)


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def asset_path(folder, name):
    return folder + "/" + name


def import_texture(key, source):
    if not source.is_file():
        fail("missing %s source %s" % (key, source))
    name = "T_LB_PS_InfeedCoilFeeder_%s_v001" % key
    path = asset_path(TEXTURE_ROOT, name)
    texture = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if texture is None:
        task = unreal.AssetImportTask()
        task.set_editor_properties({
            "filename": str(source), "destination_path": TEXTURE_ROOT,
            "destination_name": name, "automated": True,
            "replace_existing": False, "save": True,
        })
        TOOLS.import_asset_tasks([task])
        imported = list(task.get_editor_property("imported_object_paths") or [])
        if len(imported) != 1:
            fail("expected one imported %s texture, got %s" % (key, imported))
        texture = unreal.load_asset(imported[0])
    if not isinstance(texture, unreal.Texture):
        fail("%s did not resolve to Texture" % key)
    texture.set_editor_property("srgb", key == "BaseColor")
    texture.set_editor_property("compression_settings", {
        "BaseColor": unreal.TextureCompressionSettings.TC_DEFAULT,
        "MetallicRoughness": unreal.TextureCompressionSettings.TC_MASKS,
        "Normal": unreal.TextureCompressionSettings.TC_NORMALMAP,
    }[key])
    if key == "Normal":
        texture.set_editor_property("flip_green_channel", True)
    unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)
    return texture


def import_mesh():
    path = asset_path(ROOT, MESH_NAME)
    mesh = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if mesh is None:
        options = unreal.FbxImportUI()
        options.set_editor_property("import_mesh", True)
        options.set_editor_property("import_materials", False)
        options.set_editor_property("import_textures", False)
        options.set_editor_property("import_as_skeletal", False)
        options.static_mesh_import_data.set_editor_property("combine_meshes", True)
        options.static_mesh_import_data.set_editor_property("auto_generate_collision", False)
        task = unreal.AssetImportTask()
        task.set_editor_properties({
            "filename": str(FBX), "destination_path": ROOT,
            "destination_name": MESH_NAME, "automated": True,
            "replace_existing": False, "save": True, "options": options,
        })
        TOOLS.import_asset_tasks([task])
        mesh = unreal.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh):
        fail("FBX did not resolve to StaticMesh")
    bounds = mesh.get_bounding_box()
    dimensions = (bounds.max.x - bounds.min.x, bounds.max.y - bounds.min.y, bounds.max.z - bounds.min.z)
    if any(abs(actual - expected) > 4.0 for actual, expected in zip(sorted(dimensions), sorted((1638.401, 790.401, 800.0)))):
        fail("cm dimensions %s do not match the derived Blender source" % (dimensions,))
    triangles = int(mesh.get_num_triangles(0))
    if triangles <= 0 or triangles > 14181:
        fail("invalid LOD0 triangle count %s" % triangles)
    return mesh, dimensions, triangles


def node(material, klass, x, y):
    return MEL.create_material_expression(material, klass, x, y)


def texture_sample(material, parameter, texture, sampler_type, x, y, uv):
    sample = node(material, unreal.MaterialExpressionTextureSampleParameter2D, x, y)
    sample.set_editor_properties({"parameter_name": parameter, "texture": texture, "sampler_type": sampler_type})
    MEL.connect_material_expressions(uv, "", sample, "UVs")
    return sample


def channel(material, source, name, x, y):
    mask = node(material, unreal.MaterialExpressionComponentMask, x, y)
    mask.set_editor_property(name.lower(), True)
    MEL.connect_material_expressions(source, "RGB", mask, "")
    return mask


def make_material(textures):
    path = asset_path(MATERIAL_ROOT, MATERIAL_NAME)
    material = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if material is None:
        material = TOOLS.create_asset(MATERIAL_NAME, MATERIAL_ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if not isinstance(material, unreal.Material):
        fail("could not create native PBR material")
    if hasattr(MEL, "delete_all_material_expressions"):
        MEL.delete_all_material_expressions(material)
    material.set_editor_property("two_sided", False)
    uv = node(material, unreal.MaterialExpressionTextureCoordinate, -1000, 0)
    base = texture_sample(material, "BaseColorMap", textures["BaseColor"], unreal.MaterialSamplerType.SAMPLERTYPE_COLOR, -750, -180, uv)
    normal = texture_sample(material, "NormalMap", textures["Normal"], unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL, -750, 40, uv)
    metalrough = texture_sample(material, "MetallicRoughnessMap", textures["MetallicRoughness"], unreal.MaterialSamplerType.SAMPLERTYPE_MASKS, -750, 300, uv)
    MEL.connect_material_property(base, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(normal, "RGB", unreal.MaterialProperty.MP_NORMAL)
    MEL.connect_material_property(channel(material, metalrough, "B", -510, 270), "", unreal.MaterialProperty.MP_METALLIC)
    roughness = channel(material, metalrough, "G", -510, 390)
    multiply = node(material, unreal.MaterialExpressionMultiply, -260, 390)
    MEL.connect_material_expressions(roughness, "", multiply, "A")
    scalar = node(material, unreal.MaterialExpressionScalarParameter, -500, 520)
    scalar.set_editor_properties({"parameter_name": "RoughnessMultiplier", "default_value": 1.20})
    MEL.connect_material_expressions(scalar, "", multiply, "B")
    MEL.connect_material_property(multiply, "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    instance_path = asset_path(MATERIAL_ROOT, INSTANCE_NAME)
    instance = unreal.load_asset(instance_path) if unreal.EditorAssetLibrary.does_asset_exist(instance_path) else None
    if instance is None:
        instance = TOOLS.create_asset(INSTANCE_NAME, MATERIAL_ROOT, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    instance.set_editor_property("parent", material)
    for parameter, texture in (("BaseColorMap", textures["BaseColor"]), ("NormalMap", textures["Normal"]), ("MetallicRoughnessMap", textures["MetallicRoughness"])):
        MEL.set_material_instance_texture_parameter_value(instance, parameter, texture)
    MEL.set_material_instance_scalar_parameter_value(instance, "RoughnessMultiplier", 1.20)
    unreal.EditorAssetLibrary.save_loaded_asset(instance, only_if_is_dirty=False)
    return material, instance


if not FBX.is_file():
    fail("missing derived coil-free FBX")
textures = {key: import_texture(key, source) for key, source in TEXTURES.items()}
mesh, dims, triangles = import_mesh()
material, instance = make_material(textures)
mesh.set_material(0, instance)
unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)

receipt = {
    "status": "PASS__COIL_FREE_MESHY_FEEDER_NATIVE_PBR_IMPORT",
    "supersedes": "v001 attempted embedded FBX texture extraction; v002 imports the packed maps explicitly and wires a native Unreal material.",
    "map_loaded": False,
    "map_saved": False,
    "source_fbx": {"path": str(FBX), "sha256": digest(FBX)},
    "mesh": {"path": mesh.get_path_name(), "dimensions_cm": [round(value, 3) for value in dims], "triangles_lod0": triangles},
    "textures": {key: {"path": texture.get_path_name(), "source_sha256": digest(TEXTURES[key])} for key, texture in textures.items()},
    "native_material": {"master": material.get_path_name(), "instance": instance.get_path_name(), "roughness_multiplier": 1.20, "normal_green_flipped": True},
    "coil_policy": "No Meshy coil exists in this asset. It is paired only with the project-owned wrapped/bare coil actors in the candidate map.",
    "collision": "none authored; automatic collision disabled",
    "lods": "LOD0 only",
}
RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.EditorAssetLibrary.save_directory(ROOT, only_if_is_dirty=False, recursive=True)
unreal.log("COILFEEDER_NATIVE_PBR_IMPORT=" + json.dumps(receipt, sort_keys=True))
