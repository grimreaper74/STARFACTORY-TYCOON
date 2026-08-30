"""Import the cleaned one-coil hero press to an isolated Unreal candidate folder.

This creates only candidate assets and native materials.  It never loads, edits,
or saves a gameplay map.
"""
import hashlib
import json
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = PROJECT / "SourceAssets" / "Candidate" / "PressShop" / "HeroPressCell_MeshyOneCoil_v002"
FBX = SOURCE / "Runtime" / "SM_LB_PS_HeroPressCell_MeshyOneCoil_v002.fbx"
DESTINATION = "/Game/LineBoss/Candidates/PressShop/HeroPressCell_MeshyOneCoil_v002"
MATERIAL_DESTINATION = DESTINATION + "/Materials"
V001_TEXTURE_DESTINATION = "/Game/LineBoss/Candidates/PressShop/HeroPressCell_MeshyOneCoil_v001/Textures"
TEXTURE_PATHS = {
    "BaseColor": V001_TEXTURE_DESTINATION + "/T_LB_PS_HeroPressCell_MeshyOneCoil_BaseColor_v001",
    "MetallicRoughness": V001_TEXTURE_DESTINATION + "/T_LB_PS_HeroPressCell_MeshyOneCoil_MetallicRoughness_v001",
    "Normal": V001_TEXTURE_DESTINATION + "/T_LB_PS_HeroPressCell_MeshyOneCoil_Normal_v001",
}
MESH_NAME = "SM_LB_PS_HeroPressCell_MeshyOneCoil_v002"
MASTER_NAME = "M_LB_PS_HeroPressCell_MeshyOneCoil_v002"
INSTANCE_NAME = "MI_LB_PS_HeroPressCell_MeshyOneCoil_v002"
FLAT_MATERIALS = {
    "M_LB_PS_RollerDark_v002": ((0.055, 0.070, 0.085), 0.80, 0.42),
    "M_LB_PS_RollerFrame_v002": ((0.13, 0.16, 0.18), 0.70, 0.52),
    "M_LB_PS_GuideSafetyYellow_v002": ((0.93, 0.59, 0.04), 0.18, 0.42),
}
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "hero_press_cell_onecoil_unreal_import_v002.json"
EXPECTED_BOUNDS_CM = (1638.401, 790.401, 800.0)
EXPECTED_TRIANGLES = 12608

ASSET_TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
MEL = unreal.MaterialEditingLibrary


def fail(message):
    raise RuntimeError("HERO_PRESS_CELL_V002_IMPORT_FAIL: " + message)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def object_path(folder, name):
    return folder + "/" + name


def expression(material, klass, x, y):
    return MEL.create_material_expression(material, klass, x, y)


def texture_sample(material, parameter, texture, sampler_type, x, y, texcoord):
    sample = expression(material, unreal.MaterialExpressionTextureSampleParameter2D, x, y)
    sample.set_editor_properties({"parameter_name": parameter, "texture": texture, "sampler_type": sampler_type})
    MEL.connect_material_expressions(texcoord, "", sample, "UVs")
    return sample


def component_mask(material, source, channel, x, y):
    mask = expression(material, unreal.MaterialExpressionComponentMask, x, y)
    mask.set_editor_property(channel.lower(), True)
    MEL.connect_material_expressions(source, "RGB", mask, "")
    return mask


def resolve_textures():
    textures = {key: unreal.load_asset(path) for key, path in TEXTURE_PATHS.items()}
    if any(not isinstance(texture, unreal.Texture) for texture in textures.values()):
        fail("v001 packed textures must be imported before the v002 derivative")
    return textures


def import_mesh():
    if not FBX.is_file():
        fail("missing source FBX '{}'".format(FBX))
    asset_path = object_path(DESTINATION, MESH_NAME)
    mesh = unreal.load_asset(asset_path) if unreal.EditorAssetLibrary.does_asset_exist(asset_path) else None
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
    actual_bounds = (bounds.max.x - bounds.min.x, bounds.max.y - bounds.min.y, bounds.max.z - bounds.min.z)
    if any(abs(got - expected) > 3.0 for got, expected in zip(actual_bounds, EXPECTED_BOUNDS_CM)):
        fail("cm bounds {} do not match expected {}".format(actual_bounds, EXPECTED_BOUNDS_CM))
    triangles = int(mesh.get_num_triangles(0))
    if triangles != EXPECTED_TRIANGLES:
        fail("imported LOD0 triangle count {} differs from {} source triangles".format(triangles, EXPECTED_TRIANGLES))
    return mesh, tuple(round(value, 3) for value in actual_bounds), triangles


def build_body_material(textures):
    path = object_path(MATERIAL_DESTINATION, MASTER_NAME)
    master = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if master is None:
        master = ASSET_TOOLS.create_asset(MASTER_NAME, MATERIAL_DESTINATION, unreal.Material, unreal.MaterialFactoryNew())
    if not isinstance(master, unreal.Material):
        fail("could not create native body material")
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
    multiplier = expression(master, unreal.MaterialExpressionScalarParameter, -600, 500)
    multiplier.set_editor_properties({"parameter_name": "RoughnessMultiplier", "default_value": 1.30})
    adjusted = expression(master, unreal.MaterialExpressionMultiply, -360, 400)
    MEL.connect_material_expressions(roughness, "", adjusted, "A")
    MEL.connect_material_expressions(multiplier, "", adjusted, "B")
    MEL.connect_material_property(adjusted, "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(master)
    unreal.EditorAssetLibrary.save_loaded_asset(master, only_if_is_dirty=False)
    instance_path = object_path(MATERIAL_DESTINATION, INSTANCE_NAME)
    instance = unreal.load_asset(instance_path) if unreal.EditorAssetLibrary.does_asset_exist(instance_path) else None
    if instance is None:
        instance = ASSET_TOOLS.create_asset(INSTANCE_NAME, MATERIAL_DESTINATION, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    instance.set_editor_property("parent", master)
    MEL.set_material_instance_texture_parameter_value(instance, "BaseColorMap", textures["BaseColor"])
    MEL.set_material_instance_texture_parameter_value(instance, "NormalMap", textures["Normal"])
    MEL.set_material_instance_texture_parameter_value(instance, "MetallicRoughnessMap", textures["MetallicRoughness"])
    MEL.set_material_instance_scalar_parameter_value(instance, "RoughnessMultiplier", 1.30)
    unreal.EditorAssetLibrary.save_loaded_asset(instance, only_if_is_dirty=False)
    return master, instance


def build_flat_material(name, colour, metallic_value, roughness_value):
    path = object_path(MATERIAL_DESTINATION, name)
    material = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if material is None:
        material = ASSET_TOOLS.create_asset(name, MATERIAL_DESTINATION, unreal.Material, unreal.MaterialFactoryNew())
    if not isinstance(material, unreal.Material):
        fail("could not create clean roller material '{}'".format(name))
    if hasattr(MEL, "delete_all_material_expressions"):
        MEL.delete_all_material_expressions(material)
    colour_node = expression(material, unreal.MaterialExpressionConstant3Vector, -450, -120)
    colour_node.set_editor_property("constant", unreal.LinearColor(colour[0], colour[1], colour[2], 1.0))
    metallic_node = expression(material, unreal.MaterialExpressionConstant, -450, 30)
    metallic_node.set_editor_property("r", metallic_value)
    roughness_node = expression(material, unreal.MaterialExpressionConstant, -450, 170)
    roughness_node.set_editor_property("r", roughness_value)
    MEL.connect_material_property(colour_node, "", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(metallic_node, "", unreal.MaterialProperty.MP_METALLIC)
    MEL.connect_material_property(roughness_node, "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


textures = resolve_textures()
mesh, bounds_cm, triangles = import_mesh()
master, instance = build_body_material(textures)
flat_materials = {name: build_flat_material(name, *spec) for name, spec in FLAT_MATERIALS.items()}
slots = list(mesh.get_editor_property("static_materials"))
if len(slots) != 4:
    fail("expected four material slots (body + three authored clean materials), got {}".format(len(slots)))
for index, material in enumerate((instance, flat_materials["M_LB_PS_RollerDark_v002"], flat_materials["M_LB_PS_RollerFrame_v002"], flat_materials["M_LB_PS_GuideSafetyYellow_v002"])):
    mesh.set_material(index, material)
unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)

receipt = {
    "status": "PASS__CLEANED_CANDIDATE_IMPORTED_WITH_NATIVE_MATERIALS__NO_MAP_TOUCHED",
    "map_loaded": False,
    "map_saved": False,
    "source": {"fbx": str(FBX), "fbx_sha256": sha256(FBX)},
    "static_mesh": {"path": mesh.get_path_name(), "bounds_cm": bounds_cm, "triangles_lod0": triangles, "material_slot_count": len(slots)},
    "native_materials": {"body_master": master.get_path_name(), "body_instance": instance.get_path_name(), "flat_materials": {key: value.get_path_name() for key, value in flat_materials.items()}, "roughness_multiplier": 1.30},
    "collision": "not authored; import auto-generation explicitly disabled",
    "next_gate": "isolated candidate review level and human visual sign-off before any gameplay-map placement.",
}
RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.EditorAssetLibrary.save_directory(DESTINATION, only_if_is_dirty=False, recursive=True)
unreal.log("LINE_BOSS_HERO_PRESS_CELL_V002_IMPORT=" + json.dumps(receipt, sort_keys=True))
