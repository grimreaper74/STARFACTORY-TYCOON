"""Guarded textured promotion of Claude's verified S02 RuntimePrep v003 bundle.

This is deliberately a new, owned namespace: RuntimePrep v002 is retained as
evidence and is never overwritten.  The script imports the exact six v003
exports plus their deterministic PBR inputs, creates a small native material
closure, and writes a provenance receipt.  It does not place or save a map.

Run through Unreal's Python commandlet/editor after confirming the destination
does not already exist.  A preflight checks every source hash before the first
asset is created.
"""

import hashlib
import io
import json
import os

import unreal


PROJECT_ROOT = r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8"
SOURCE_ASSET_DIR = PROJECT_ROOT + "/ArtSource/Claude_S02_DeepDraw_v003"
SOURCE_PREP_DIR = PROJECT_ROOT + "/ArtSource/Claude_S02_DeepDraw_RuntimePrep_v003"
DESTINATION = (
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
    "DetailedPresentation_v001/S02DeepDraw_v003"
)
TEXTURE_DESTINATION = DESTINATION + "/Textures"
MATERIAL_DESTINATION = DESTINATION + "/Materials"
RECEIPT = (
    PROJECT_ROOT
    + "/Saved/Audits/OneFactory/Press/S02DeepDrawRuntimePrep_v003/import_receipt.json"
)

EXPORTS = (
    {
        "key": "Static",
        "fbx": "CA_S02_DeepDraw_Static_LOD0.fbx",
        "asset_name": "SM_CA_S02DeepDraw_Static_LOD0_v003",
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
        "asset_name": "SM_CA_S02DeepDraw_Ram_LOD0_v003",
        "dimensions_cm": (222.0, 180.0, 188.0),
        "material_slots": ("M_CA_DarkSteel",),
    },
    {
        "key": "Blankholder",
        "fbx": "CA_S02_DeepDraw_Blankholder_LOD0.fbx",
        "asset_name": "SM_CA_S02DeepDraw_Blankholder_LOD0_v003",
        "dimensions_cm": (190.0, 155.0, 12.0),
        "material_slots": ("M_CA_CleanSteel",),
    },
    {
        "key": "Bolster",
        "fbx": "CA_S02_DeepDraw_Bolster_LOD0.fbx",
        "asset_name": "SM_CA_S02DeepDraw_Bolster_LOD0_v003",
        "dimensions_cm": (210.0, 200.0, 36.0),
        "material_slots": ("M_CA_CleanSteel",),
    },
    {
        "key": "Flywheel",
        "fbx": "CA_S02_DeepDraw_Flywheel_LOD0.fbx",
        "asset_name": "SM_CA_S02DeepDraw_Flywheel_LOD0_v003",
        "dimensions_cm": (194.0, 43.0, 194.0),
        "material_slots": ("M_CA_DarkSteel",),
    },
    {
        "key": "SafetyGate",
        "fbx": "CA_S02_DeepDraw_SafetyGate_LOD0.fbx",
        "asset_name": "SM_CA_S02DeepDraw_SafetyGate_LOD0_v003",
        "dimensions_cm": (92.0, 11.5, 160.0),
        "material_slots": ("M_CA_SafetyYellow",),
    },
)

FAMILY_BY_SLOT = {
    "M_CA_MainGreen": "MainGreen",
    "M_CA_Concrete": "Concrete",
    "M_CA_DarkSteel": "DarkSteel",
    "M_CA_CleanSteel": "CleanSteel",
    "M_CA_CharcoalGrey": "CharcoalGrey",
    "M_CA_SafetyYellow": "SafetyYellow",
    "M_CA_ScreenDark": "ScreenDark",
    "M_CA_LampGreen": "LampGreen",
    "M_CA_LampAmber": "LampAmber",
    "M_CA_LampRed": "LampRed",
}

# The source masks are already baked into BC/ORM.  These values only give the
# raw dust channel a restrained, inspectable contribution in-engine; they do
# not replace the authored PBR look.  Lamps stay clean and use modest emission.
FAMILY_TUNING = {
    "MainGreen": {"dust": 0.07, "emission": 0.0},
    "Concrete": {"dust": 0.05, "emission": 0.0},
    "DarkSteel": {"dust": 0.04, "emission": 0.0},
    "CleanSteel": {"dust": 0.025, "emission": 0.0},
    "CharcoalGrey": {"dust": 0.045, "emission": 0.0},
    "SafetyYellow": {"dust": 0.035, "emission": 0.0},
    "ScreenDark": {"dust": 0.01, "emission": 0.0},
    "LampGreen": {"dust": 0.0, "emission": 1.5},
    "LampAmber": {"dust": 0.0, "emission": 1.2},
    "LampRed": {"dust": 0.0, "emission": 0.75},
}


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().lower()


def fail(message):
    raise RuntimeError("S02 RuntimePrep v003 import failed: {}".format(message))


def object_path(folder, name):
    return "{0}/{1}.{1}".format(folder, name)


def source_texture_specs(manifest, stats):
    specs = []
    for family, row in sorted(manifest["families"].items()):
        for channel, map_row in sorted(row["maps"].items()):
            file_path = SOURCE_ASSET_DIR + "/" + map_row["file"]
            asset_name = os.path.splitext(os.path.basename(file_path))[0]
            specs.append({
                "family": family,
                "channel": channel,
                "source_path": file_path,
                "asset_name": asset_name,
                "source_sha256": map_row["sha256"].lower(),
            })
    for module, row in sorted(stats["ao_bakes"].items()):
        file_path = SOURCE_PREP_DIR + "/" + row["file"]
        asset_name = os.path.splitext(os.path.basename(file_path))[0]
        specs.append({
            "family": None,
            "channel": "AO",
            "module": module,
            "source_path": file_path,
            "asset_name": asset_name,
            "source_sha256": row["sha256"].lower(),
        })
    return specs


def preflight(manifest, stats):
    destination_exists = unreal.EditorAssetLibrary.does_directory_exist(DESTINATION)
    if destination_exists and os.path.isfile(RECEIPT):
        fail("destination already has a completed immutable v003 receipt: {}".format(
            DESTINATION))
    if manifest.get("asset") != "CA_S02_DeepDraw_v003":
        fail("texture manifest is not the declared S02 v003 authority")
    if stats.get("original_total_triangles") != 5664:
        fail("RuntimePrep stats do not record the approved 5,664 triangles")
    if stats.get("source_deviation_check", {}).get("error_m") != 0.0:
        fail("DieUpper source gate is not clean in RuntimePrep stats")
    for spec in EXPORTS:
        source_fbx = SOURCE_PREP_DIR + "/" + spec["fbx"]
        if not os.path.isfile(source_fbx):
            fail("RuntimePrep source is missing: {}".format(source_fbx))
    for texture_spec in source_texture_specs(manifest, stats):
        if not os.path.isfile(texture_spec["source_path"]):
            fail("texture source is missing: {}".format(texture_spec["source_path"]))
        actual_hash = sha256(texture_spec["source_path"])
        if actual_hash != texture_spec["source_sha256"]:
            fail("texture source hash drifted for {}: {} != {}".format(
                texture_spec["asset_name"], actual_hash,
                texture_spec["source_sha256"]))
    # A prior editor run can be interrupted after importing immutable source
    # assets but before building the material closure.  Recover only that exact
    # known partial state.  A completed receipt above remains fail-closed.
    if destination_exists:
        for spec in EXPORTS:
            expected_path = object_path(DESTINATION, spec["asset_name"])
            if not unreal.EditorAssetLibrary.does_asset_exist(expected_path):
                fail("partial v003 recovery is missing already-imported mesh {}".format(
                    expected_path))
        for texture_spec in source_texture_specs(manifest, stats):
            expected_path = object_path(TEXTURE_DESTINATION,
                texture_spec["asset_name"])
            if not unreal.EditorAssetLibrary.does_asset_exist(expected_path):
                fail("partial v003 recovery is missing already-imported texture {}".format(
                    expected_path))


def configure_texture(texture, channel):
    try:
        if channel == "BC":
            texture.set_editor_property("srgb", True)
            texture.set_editor_property(
                "compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)
        elif channel == "N":
            texture.set_editor_property("srgb", False)
            texture.set_editor_property(
                "compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
            # Claude's normal maps are OpenGL +Y.  Store the conversion on the
            # texture so the shared master can use a normal sampler directly.
            texture.set_editor_property("flip_green_channel", True)
        else:
            texture.set_editor_property("srgb", False)
            texture.set_editor_property(
                "compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
    except Exception as error:
        fail("cannot set required {} texture import settings on {}: {}".format(
            channel, texture.get_name(), error))
    unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)


def import_texture(spec):
    expected_path = object_path(TEXTURE_DESTINATION, spec["asset_name"])
    if unreal.EditorAssetLibrary.does_asset_exist(expected_path):
        imported_path = expected_path
    else:
        task = unreal.AssetImportTask()
        task.set_editor_property("filename", spec["source_path"])
        task.set_editor_property("destination_path", TEXTURE_DESTINATION)
        task.set_editor_property("destination_name", spec["asset_name"])
        task.set_editor_property("automated", True)
        task.set_editor_property("replace_existing", False)
        task.set_editor_property("save", True)
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        imported_paths = list(task.get_editor_property("imported_object_paths") or [])
        if len(imported_paths) != 1:
            fail("expected one texture for {} but got {}: {}".format(
                spec["asset_name"], len(imported_paths), imported_paths))
        imported_path = imported_paths[0]
    texture = unreal.load_asset(imported_path)
    if not isinstance(texture, unreal.Texture):
        fail("{} did not resolve to a texture".format(spec["asset_name"]))
    configure_texture(texture, spec["channel"])
    expected_srgb = spec["channel"] == "BC"
    if texture.get_editor_property("srgb") != expected_srgb:
        fail("{} sRGB setting drifted after save".format(spec["asset_name"]))
    if spec["channel"] == "N" and not texture.get_editor_property("flip_green_channel"):
        fail("{} did not retain the required OpenGL green flip".format(
            spec["asset_name"]))
    return texture


def import_mesh(spec):
    source_fbx = SOURCE_PREP_DIR + "/" + spec["fbx"]
    expected_path = object_path(DESTINATION, spec["asset_name"])
    if unreal.EditorAssetLibrary.does_asset_exist(expected_path):
        imported_path = expected_path
    else:
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
        imported_path = imported_paths[0]
    mesh = unreal.load_asset(imported_path)
    if mesh is None or not isinstance(mesh, unreal.StaticMesh):
        fail("{} did not resolve to a StaticMesh".format(spec["key"]))

    bounds = mesh.get_bounding_box()
    size = bounds.max - bounds.min
    dimensions = (round(size.x, 2), round(size.y, 2), round(size.z, 2))
    if any(abs(actual - expected) > 3.0
           for actual, expected in zip(dimensions, spec["dimensions_cm"])):
        fail("{} bounds differ from RuntimePrep receipt: got {}, expected {}".format(
            spec["key"], dimensions, spec["dimensions_cm"]))

    slots = tuple(str(slot.material_slot_name) for slot in mesh.static_materials)
    if slots != spec["material_slots"]:
        fail("{} semantic material slots differ: got {}, expected {}".format(
            spec["key"], slots, spec["material_slots"]))

    return {
        "source_fbx": source_fbx,
        "source_fbx_sha256": sha256(source_fbx),
        "mesh_object_path": imported_path,
        "dimensions_cm": dimensions,
        "material_slots": slots,
        "combined_meshes": True,
    }


def expression(material, klass, x, y):
    return unreal.MaterialEditingLibrary.create_material_expression(material, klass, x, y)


def build_master(default_textures):
    name = "M_CA_S02DeepDraw_PBR_Master_v003"
    master_path = object_path(MATERIAL_DESTINATION, name)
    master = unreal.load_asset(master_path) if unreal.EditorAssetLibrary.does_asset_exist(
        master_path) else None
    if master is None:
        master = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, MATERIAL_DESTINATION, unreal.Material, unreal.MaterialFactoryNew())
    editing = unreal.MaterialEditingLibrary
    if hasattr(editing, "delete_all_material_expressions"):
        editing.delete_all_material_expressions(master)
    master.set_editor_property("two_sided", False)

    uv0 = expression(master, unreal.MaterialExpressionTextureCoordinate, -1050, 0)
    uv0.set_editor_property("coordinate_index", 0)
    uv1 = expression(master, unreal.MaterialExpressionTextureCoordinate, -1050, 750)
    uv1.set_editor_property("coordinate_index", 1)

    def sample_parameter(name, texture, sampler_type, x, y, uv):
        node = expression(master, unreal.MaterialExpressionTextureSampleParameter2D, x, y)
        node.set_editor_properties({
            "parameter_name": name,
            "texture": texture,
            "sampler_type": sampler_type,
        })
        editing.connect_material_expressions(uv, "", node, "UVs")
        return node

    base = sample_parameter("BaseColorMap", default_textures["BC"],
        unreal.MaterialSamplerType.SAMPLERTYPE_COLOR, -820, -160, uv0)
    normal = sample_parameter("NormalMap", default_textures["N"],
        unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL, -820, 210, uv0)
    orm = sample_parameter("ORMMap", default_textures["ORM"],
        unreal.MaterialSamplerType.SAMPLERTYPE_MASKS, -820, 430, uv0)
    mask = sample_parameter("WearMaskMap", default_textures["MASK"],
        unreal.MaterialSamplerType.SAMPLERTYPE_MASKS, -820, 630, uv0)
    ao = sample_parameter("ModuleAOMap", default_textures["AO"],
        unreal.MaterialSamplerType.SAMPLERTYPE_MASKS, -820, 830, uv1)

    # Optional raw dust uses the source mask non-destructively: it is a small
    # multiplier on top of the already composited BaseColor and is tunable per
    # material instance.  This retains a documented runtime seam for art review.
    dust_mask = expression(master, unreal.MaterialExpressionComponentMask, -580, 630)
    dust_mask.set_editor_property("b", True)
    editing.connect_material_expressions(mask, "RGB", dust_mask, "")
    dust_strength = expression(master, unreal.MaterialExpressionScalarParameter, -580, 730)
    dust_strength.set_editor_properties({"parameter_name": "RawDustStrength", "default_value": 0.0})
    dust_alpha = expression(master, unreal.MaterialExpressionMultiply, -360, 670)
    editing.connect_material_expressions(dust_mask, "", dust_alpha, "A")
    editing.connect_material_expressions(dust_strength, "", dust_alpha, "B")
    darken = expression(master, unreal.MaterialExpressionConstant3Vector, -580, -30)
    darken.set_editor_property("constant", unreal.LinearColor(0.76, 0.76, 0.76, 1.0))
    dusty_base = expression(master, unreal.MaterialExpressionMultiply, -360, -110)
    editing.connect_material_expressions(base, "RGB", dusty_base, "A")
    editing.connect_material_expressions(darken, "", dusty_base, "B")
    base_lerp = expression(master, unreal.MaterialExpressionLinearInterpolate, -120, -110)
    editing.connect_material_expressions(base, "RGB", base_lerp, "A")
    editing.connect_material_expressions(dusty_base, "", base_lerp, "B")
    editing.connect_material_expressions(dust_alpha, "", base_lerp, "Alpha")
    editing.connect_material_property(base_lerp, "", unreal.MaterialProperty.MP_BASE_COLOR)

    editing.connect_material_property(normal, "RGB", unreal.MaterialProperty.MP_NORMAL)
    orm_ao = expression(master, unreal.MaterialExpressionComponentMask, -580, 430)
    orm_ao.set_editor_property("r", True)
    editing.connect_material_expressions(orm, "RGB", orm_ao, "")
    baked_ao = expression(master, unreal.MaterialExpressionComponentMask, -580, 830)
    baked_ao.set_editor_property("r", True)
    editing.connect_material_expressions(ao, "RGB", baked_ao, "")
    multiplied_ao = expression(master, unreal.MaterialExpressionMultiply, -350, 500)
    editing.connect_material_expressions(orm_ao, "", multiplied_ao, "A")
    editing.connect_material_expressions(baked_ao, "", multiplied_ao, "B")
    editing.connect_material_property(multiplied_ao, "", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    orm_roughness = expression(master, unreal.MaterialExpressionComponentMask, -580, 500)
    orm_roughness.set_editor_property("g", True)
    editing.connect_material_expressions(orm, "RGB", orm_roughness, "")
    editing.connect_material_property(orm_roughness, "", unreal.MaterialProperty.MP_ROUGHNESS)
    orm_metallic = expression(master, unreal.MaterialExpressionComponentMask, -580, 560)
    orm_metallic.set_editor_property("b", True)
    editing.connect_material_expressions(orm, "RGB", orm_metallic, "")
    editing.connect_material_property(orm_metallic, "", unreal.MaterialProperty.MP_METALLIC)

    emission_strength = expression(master, unreal.MaterialExpressionScalarParameter, -120, 100)
    emission_strength.set_editor_properties({"parameter_name": "EmissionStrength", "default_value": 0.0})
    emission = expression(master, unreal.MaterialExpressionMultiply, 100, 30)
    editing.connect_material_expressions(base_lerp, "", emission, "A")
    editing.connect_material_expressions(emission_strength, "", emission, "B")
    editing.connect_material_property(emission, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    editing.recompile_material(master)
    unreal.EditorAssetLibrary.save_loaded_asset(master, only_if_is_dirty=False)
    return master


def build_instance(module, family, textures, master):
    name = "MI_CA_S02DeepDraw_{0}_{1}_v003".format(module, family)
    instance_path = object_path(MATERIAL_DESTINATION, name)
    instance = unreal.load_asset(instance_path) if unreal.EditorAssetLibrary.does_asset_exist(
        instance_path) else None
    if instance is None:
        instance = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, MATERIAL_DESTINATION, unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew())
    instance.set_editor_property("parent", master)
    editing = unreal.MaterialEditingLibrary
    editing.set_material_instance_texture_parameter_value(
        instance, "BaseColorMap", textures[family]["BC"])
    editing.set_material_instance_texture_parameter_value(
        instance, "NormalMap", textures[family]["N"])
    editing.set_material_instance_texture_parameter_value(
        instance, "ORMMap", textures[family]["ORM"])
    editing.set_material_instance_texture_parameter_value(
        instance, "WearMaskMap", textures[family]["MASK"])
    editing.set_material_instance_texture_parameter_value(
        instance, "ModuleAOMap", textures["AO"][module])
    tuning = FAMILY_TUNING[family]
    editing.set_material_instance_scalar_parameter_value(
        instance, "RawDustStrength", tuning["dust"])
    editing.set_material_instance_scalar_parameter_value(
        instance, "EmissionStrength", tuning["emission"])
    unreal.EditorAssetLibrary.save_loaded_asset(instance, only_if_is_dirty=False)
    return instance


def build_materials(texture_specs, texture_assets):
    textures = {family: {} for family in FAMILY_BY_SLOT.values()}
    textures["AO"] = {}
    for spec in texture_specs:
        texture = texture_assets[spec["asset_name"]]
        if spec["channel"] == "AO":
            textures["AO"][spec["module"]] = texture
        else:
            textures[spec["family"]][spec["channel"]] = texture
    for family in FAMILY_BY_SLOT.values():
        if set(textures[family]) != {"BC", "N", "ORM", "MASK"}:
            fail("incomplete imported PBR family: {}".format(family))
    if set(textures["AO"]) != {spec["key"] for spec in EXPORTS}:
        fail("incomplete imported module AO set")

    defaults = dict(textures["MainGreen"])
    defaults["AO"] = textures["AO"]["Static"]
    master = build_master(defaults)
    material_assets = {}
    for spec in EXPORTS:
        for slot in spec["material_slots"]:
            family = FAMILY_BY_SLOT[slot]
            material_assets[(spec["key"], slot)] = build_instance(
                spec["key"], family, textures, master)
    return master, material_assets


with io.open(SOURCE_ASSET_DIR + "/texture_material_manifest.json", "r", encoding="utf-8") as handle:
    texture_manifest = json.load(handle)
with io.open(SOURCE_PREP_DIR + "/runtime_prep_stats.json", "r", encoding="utf-8") as handle:
    runtime_stats = json.load(handle)

preflight(texture_manifest, runtime_stats)
texture_specs = source_texture_specs(texture_manifest, runtime_stats)
texture_assets = {}
for texture_spec in texture_specs:
    texture_assets[texture_spec["asset_name"]] = import_texture(texture_spec)

mesh_results = {}
for export_spec in EXPORTS:
    mesh_results[export_spec["key"]] = import_mesh(export_spec)

master_material, material_assets = build_materials(texture_specs, texture_assets)

receipt = {
    "schema": "lineboss/onefactory/press/s02-deepdraw-runtimeprep-v003-import/v1",
    "status": "PASS__TEXTURED_RUNTIMEPREP_V003_IMPORTED_AT_RECEIPTED_UNREAL_SCALE",
    "destination": DESTINATION,
    "source_asset": SOURCE_ASSET_DIR,
    "source_runtimeprep": SOURCE_PREP_DIR,
    "source_blend_sha256": runtime_stats["source_blend_sha256"],
    "modules": mesh_results,
    "texture_manifest_sha256": sha256(SOURCE_ASSET_DIR + "/texture_material_manifest.json"),
    "runtime_prep_stats_sha256": sha256(SOURCE_PREP_DIR + "/runtime_prep_stats.json"),
    "textures": {
        name: texture.get_path_name() for name, texture in sorted(texture_assets.items())
    },
    "material_master": master_material.get_path_name(),
    "module_materials": {
        "{0}:{1}".format(module, slot): material.get_path_name()
        for (module, slot), material in sorted(material_assets.items())
    },
    "imported_materials_from_fbx": False,
    "imported_textures_from_fbx": False,
    "native_material_closure": True,
    "normal_maps_green_flipped": True,
    "auto_generated_collision": False,
    "map_loaded": False,
    "map_saved": False,
}
os.makedirs(os.path.dirname(RECEIPT), exist_ok=True)
with io.open(RECEIPT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")

unreal.EditorAssetLibrary.save_directory(DESTINATION, only_if_is_dirty=False, recursive=True)
unreal.log("LINE_BOSS_S02_RUNTIMEPREP_V003_IMPORT=" + json.dumps(receipt, sort_keys=True))
