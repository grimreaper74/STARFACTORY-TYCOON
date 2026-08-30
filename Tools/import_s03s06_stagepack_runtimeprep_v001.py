"""Fail-closed native import of Claude's textured S03--S06 StagePack v001.

The source package is an immutable, verified Blender handoff.  This importer
creates a separate native Unreal closure for its eleven RuntimePrep meshes,
the supplied nine-family PBR texture set, and a small shared material master.
It never loads or saves a map, never touches Candidate content, and refuses to
overwrite a prior result.  The receipt is deliberately enough to prove the
source-to-native handoff without relying on a chat transcript.
"""

import hashlib
import io
import json
import os

import unreal


PROJECT_ROOT = r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8"
SOURCE_ASSET_DIR = PROJECT_ROOT + "/ArtSource/Claude_S03S06_StagePack_v001"
SOURCE_PREP_DIR = PROJECT_ROOT + "/ArtSource/Claude_S03S06_StagePack_RuntimePrep_v001"
DESTINATION = (
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
    "SharedTrainModules_v003"
)
MESH_DESTINATION = DESTINATION + "/Meshes"
TEXTURE_DESTINATION = DESTINATION + "/Textures"
MATERIAL_DESTINATION = DESTINATION + "/Materials"
RECEIPT = (
    PROJECT_ROOT
    + "/Saved/Audits/OneFactory/Press/S03S06StagePackRuntimePrep_v001/"
    "import_receipt.json"
)


# These are the published RuntimePrep contract values, not estimates from a
# render.  Keeping them local gives the import lane a concrete mismatch gate.
EXPORTS = (
    {
        "key": "S03_Frame",
        "fbx": "CA_PTA_S03_Frame_Form_LOD0.fbx",
        "asset_name": "SM_CA_MW_PT_S03_Frame_Form_LOD0_v001",
        "dimensions_cm": (648.0, 620.0, 950.0),
        "triangles": 1296,
        "unreal_render_triangles": 8496,
        "material_slots": (
            "CA_MW_FoundryCharcoal", "CA_MW_CairnwellGreen",
            "CA_MW_ServiceGrey", "CA_MW_SafetyYellow",
            "CA_MW_InspectionGlass", "CA_MW_TrainAAccent",
            "CA_MW_WorkedSteel",
        ),
    },
    {
        "key": "S03_Cue",
        "fbx": "CA_PTA_S03_Cue_SecondaryForm_LOD0.fbx",
        "asset_name": "SM_CA_MW_PT_S03_Cue_SecondaryForm_LOD0_v001",
        "dimensions_cm": (56.5, 222.0, 178.0),
        "triangles": 2432,
        "unreal_render_triangles": 2432,
        "material_slots": (
            "CA_MW_FoundryCharcoal", "CA_MW_ServiceGrey",
            "CA_MW_CairnwellGreen", "CA_MW_WorkedSteel",
            "CA_MW_TrainAAccent", "CA_MW_SafetyYellow",
            "CA_MW_StatusGreen",
        ),
    },
    {
        "key": "S04_Frame",
        "fbx": "CA_PTA_S04_Frame_Trim_LOD0.fbx",
        "asset_name": "SM_CA_MW_PT_S04_Frame_Trim_LOD0_v001",
        "dimensions_cm": (648.0, 620.0, 900.0),
        "triangles": 1308,
        "unreal_render_triangles": 8700,
        "material_slots": (
            "CA_MW_FoundryCharcoal", "CA_MW_CairnwellGreen",
            "CA_MW_ServiceGrey", "CA_MW_SafetyYellow",
            "CA_MW_InspectionGlass", "CA_MW_TrainAAccent",
            "CA_MW_WorkedSteel",
        ),
    },
    {
        "key": "S04_Cue",
        "fbx": "CA_PTA_S04_Cue_TrimScrap_LOD0.fbx",
        "asset_name": "SM_CA_MW_PT_S04_Cue_TrimScrap_LOD0_v001",
        "dimensions_cm": (68.0, 232.0, 225.0),
        "triangles": 972,
        "unreal_render_triangles": 972,
        "material_slots": (
            "CA_MW_FoundryCharcoal", "CA_MW_ServiceGrey",
            "CA_MW_SafetyYellow", "CA_MW_CairnwellGreen",
            "CA_MW_WorkedSteel", "CA_MW_StatusAmber",
        ),
    },
    {
        "key": "S05_Frame",
        "fbx": "CA_PTA_S05_Frame_Pierce_LOD0.fbx",
        "asset_name": "SM_CA_MW_PT_S05_Frame_Pierce_LOD0_v001",
        "dimensions_cm": (648.0, 620.0, 850.0),
        "triangles": 1308,
        "unreal_render_triangles": 8700,
        "material_slots": (
            "CA_MW_FoundryCharcoal", "CA_MW_CairnwellGreen",
            "CA_MW_ServiceGrey", "CA_MW_SafetyYellow",
            "CA_MW_InspectionGlass", "CA_MW_TrainAAccent",
            "CA_MW_WorkedSteel",
        ),
    },
    {
        "key": "S05_Cue",
        "fbx": "CA_PTA_S05_Cue_PierceSlug_LOD0.fbx",
        "asset_name": "SM_CA_MW_PT_S05_Cue_PierceSlug_LOD0_v001",
        "dimensions_cm": (71.5, 226.0, 224.0),
        "triangles": 2052,
        "unreal_render_triangles": 1956,
        "material_slots": (
            "CA_MW_FoundryCharcoal", "CA_MW_ServiceGrey",
            "CA_MW_CairnwellGreen", "CA_MW_StatusAmber",
            "CA_MW_SafetyYellow", "CA_MW_WorkedSteel",
        ),
    },
    {
        "key": "S06_Frame",
        "fbx": "CA_PTA_S06_Frame_Flange_LOD0.fbx",
        "asset_name": "SM_CA_MW_PT_S06_Frame_Flange_LOD0_v001",
        "dimensions_cm": (648.0, 620.0, 900.0),
        "triangles": 1296,
        "unreal_render_triangles": 8592,
        "material_slots": (
            "CA_MW_FoundryCharcoal", "CA_MW_CairnwellGreen",
            "CA_MW_ServiceGrey", "CA_MW_SafetyYellow",
            "CA_MW_InspectionGlass", "CA_MW_TrainAAccent",
            "CA_MW_WorkedSteel",
        ),
    },
    {
        "key": "S06_Cue",
        "fbx": "CA_PTA_S06_Cue_RestrikeQuality_LOD0.fbx",
        "asset_name": "SM_CA_MW_PT_S06_Cue_RestrikeQuality_LOD0_v001",
        "dimensions_cm": (54.5, 224.0, 178.0),
        "triangles": 3352,
        "unreal_render_triangles": 3352,
        "material_slots": (
            "CA_MW_FoundryCharcoal", "CA_MW_WorkedSteel",
            "CA_MW_CairnwellGreen", "CA_MW_StatusGreen",
            "CA_MW_TrainAAccent",
        ),
    },
    {
        "key": "Shared_PressSlide",
        "fbx": "CA_PTA_Shared_PressSlide_LOD0.fbx",
        "asset_name": "SM_CA_MW_PT_Shared_PressSlide_LOD0_v001",
        "dimensions_cm": (500.0, 420.0, 87.0),
        "triangles": 24,
        "unreal_render_triangles": 216,
        "material_slots": ("CA_MW_WorkedSteel", "CA_MW_ServiceGrey"),
    },
    {
        "key": "Shared_MovingBolster",
        "fbx": "CA_PTA_Shared_MovingBolster_LOD0.fbx",
        "asset_name": "SM_CA_MW_PT_Shared_MovingBolster_LOD0_v001",
        "dimensions_cm": (520.0, 500.0, 50.0),
        "triangles": 316,
        "unreal_render_triangles": 1052,
        "material_slots": ("CA_MW_WorkedSteel", "CA_MW_ServiceGrey"),
    },
    {
        "key": "Shared_StageDieSet",
        "fbx": "CA_PTA_Shared_StageDieSet_LOD0.fbx",
        "asset_name": "SM_CA_MW_PT_Shared_StageDieSet_LOD0_v001",
        "dimensions_cm": (480.0, 360.0, 95.0),
        "triangles": 296,
        "unreal_render_triangles": 1064,
        "material_slots": (
            "CA_MW_WorkedSteel", "CA_MW_ServiceGrey", "CA_MW_SafetyYellow",
        ),
    },
)

FAMILIES = (
    "CairnwellGreen", "FoundryCharcoal", "ServiceGrey", "SafetyYellow",
    "WorkedSteel", "InspectionGlass", "TrainAAccent", "StatusGreen",
    "StatusAmber",
)
SLOT_TO_FAMILY = {"CA_MW_{}".format(family): family for family in FAMILIES}
FAMILY_DUST = {
    "CairnwellGreen": 0.035,
    "FoundryCharcoal": 0.050,
    "ServiceGrey": 0.030,
    "SafetyYellow": 0.020,
    "WorkedSteel": 0.015,
    "InspectionGlass": 0.0,
    "TrainAAccent": 0.020,
    # Source status indicators are explicitly coloured, opaque, and non-emissive.
    "StatusGreen": 0.0,
    "StatusAmber": 0.0,
}


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().lower()


def fail(message):
    raise RuntimeError("S03-S06 StagePack RuntimePrep v001 import failed: {}".format(
        message))


def object_path(folder, name):
    return "{0}/{1}.{1}".format(folder, name)


def texture_specs(texture_manifest):
    specs = []
    families = texture_manifest.get("families", {})
    if set(families) != set(FAMILIES):
        fail("texture family contract drifted: {}".format(sorted(families)))
    for family in FAMILIES:
        family_row = families[family]
        expected_slot = "CA_MW_{}".format(family)
        if family_row.get("material_slot") != expected_slot:
            fail("{} slot contract drifted".format(family))
        maps = family_row.get("maps", {})
        if set(maps) != {"BC", "N", "ORM", "MASK"}:
            fail("{} texture channels drifted: {}".format(family, sorted(maps)))
        for channel in ("BC", "N", "ORM", "MASK"):
            map_row = maps[channel]
            source_path = SOURCE_ASSET_DIR + "/" + map_row["file"]
            specs.append({
                "family": family,
                "channel": channel,
                "source_path": source_path,
                "asset_name": os.path.splitext(os.path.basename(source_path))[0],
                "source_sha256": map_row["sha256"].lower(),
            })
    return specs


def preflight(stage_manifest, texture_manifest, runtime_stats):
    if unreal.EditorAssetLibrary.does_directory_exist(DESTINATION):
        fail("destination already exists; refusing to overwrite immutable native content: {}"
             .format(DESTINATION))
    if os.path.exists(RECEIPT):
        fail("completed or partial receipt already exists: {}".format(RECEIPT))
    if stage_manifest.get("asset_pack") != "CA_PTA_S03S06_StagePack_v001":
        fail("stage manifest is not the declared StagePack v001 authority")
    if runtime_stats.get("source_blend_sha256") != "0f8fa313a7e82e08b5fdf053418a94ea732bd5bfd6b3700376083e6b55a10fd0":
        fail("unexpected StagePack source blend provenance")
    source_blend = SOURCE_ASSET_DIR + "/CA_PTA_S03S06_StagePack_v001.blend"
    if not os.path.isfile(source_blend) or sha256(source_blend) != runtime_stats["source_blend_sha256"]:
        fail("source blend is missing or has drifted from RuntimePrep provenance")
    if runtime_stats.get("reconstruction", {}).get("exported_triangles_total") != 14652:
        fail("RuntimePrep does not record the approved 14,652 exported triangles")
    if runtime_stats.get("reconstruction", {}).get("assembly_bounds_error_m") != 0.0:
        fail("RuntimePrep reconstruction is not zero-error")
    if not runtime_stats.get("reconstruction", {}).get("triangles_match_source"):
        fail("RuntimePrep triangle conservation is not recorded as true")

    exports = runtime_stats.get("exports", {})
    if set(exports) != {spec["key"] for spec in EXPORTS}:
        fail("RuntimePrep export keys drifted: {}".format(sorted(exports)))
    for spec in EXPORTS:
        record = exports[spec["key"]]
        if (record.get("file") != spec["fbx"] or
                record.get("triangles") != spec["triangles"] or
                tuple(record.get("material_slots", ())) != spec["material_slots"]):
            fail("RuntimePrep mesh contract drifted for {}".format(spec["key"]))
        source_fbx = SOURCE_PREP_DIR + "/" + spec["fbx"]
        if not os.path.isfile(source_fbx):
            fail("RuntimePrep FBX is missing: {}".format(source_fbx))
        if sha256(source_fbx) != record.get("fbx_sha256", "").lower():
            fail("RuntimePrep FBX hash drifted: {}".format(spec["fbx"]))

    for spec in texture_specs(texture_manifest):
        if not os.path.isfile(spec["source_path"]):
            fail("texture source is missing: {}".format(spec["source_path"]))
        if sha256(spec["source_path"]) != spec["source_sha256"]:
            fail("texture source hash drifted: {}".format(spec["asset_name"]))


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
            texture.set_editor_property("flip_green_channel", True)
        else:
            texture.set_editor_property("srgb", False)
            texture.set_editor_property(
                "compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
    except Exception as error:
        fail("cannot apply {} settings to {}: {}".format(
            channel, texture.get_name(), error))
    if not unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False):
        fail("cannot save imported texture {}".format(texture.get_name()))


def import_texture(spec):
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": spec["source_path"],
        "destination_path": TEXTURE_DESTINATION,
        "destination_name": spec["asset_name"],
        "automated": True,
        "replace_existing": False,
        "save": True,
    })
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported_paths = list(task.get_editor_property("imported_object_paths") or [])
    if len(imported_paths) != 1:
        fail("expected one texture for {} but got {}: {}".format(
            spec["asset_name"], len(imported_paths), imported_paths))
    texture = unreal.load_asset(imported_paths[0])
    if texture is None or not isinstance(texture, unreal.Texture):
        fail("{} did not resolve to a Texture".format(spec["asset_name"]))
    configure_texture(texture, spec["channel"])
    if texture.get_editor_property("srgb") != (spec["channel"] == "BC"):
        fail("{} sRGB setting drifted after save".format(spec["asset_name"]))
    if spec["channel"] == "N" and not texture.get_editor_property("flip_green_channel"):
        fail("{} lost the required OpenGL green flip".format(spec["asset_name"]))
    return texture


def import_mesh(spec):
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True,
        "import_materials": False,
        "import_textures": False,
        "import_as_skeletal": False,
        "automated_import_should_detect_type": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    options.static_mesh_import_data.set_editor_properties({
        "combine_meshes": True,
        "auto_generate_collision": False,
        # RuntimePrep already contains UV0 and UV1.  Do not replace the authored
        # unique channel with an auto-generated approximation.
        "generate_lightmap_u_vs": False,
        "import_uniform_scale": 1.0,
        "convert_scene": True,
        "convert_scene_unit": True,
        "force_front_x_axis": False,
    })
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": SOURCE_PREP_DIR + "/" + spec["fbx"],
        "destination_path": MESH_DESTINATION,
        "destination_name": spec["asset_name"],
        "automated": True,
        "replace_existing": False,
        "save": True,
        "options": options,
    })
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported_paths = list(task.get_editor_property("imported_object_paths") or [])
    if len(imported_paths) != 1:
        fail("expected one combined StaticMesh for {} but got {}: {}".format(
            spec["key"], len(imported_paths), imported_paths))
    mesh = unreal.load_asset(imported_paths[0])
    if mesh is None or not isinstance(mesh, unreal.StaticMesh):
        fail("{} did not resolve to a StaticMesh".format(spec["key"]))
    return mesh, imported_paths[0]


def verify_mesh(spec, mesh, mesh_path, mesh_editor):
    bounds = mesh.get_bounding_box()
    size = bounds.max - bounds.min
    dimensions = (round(size.x, 2), round(size.y, 2), round(size.z, 2))
    if any(abs(actual - expected) > 3.0
           for actual, expected in zip(dimensions, spec["dimensions_cm"])):
        fail("{} bounds differ from RuntimePrep: got {}, expected {}".format(
            spec["key"], dimensions, spec["dimensions_cm"]))
    unreal_render_triangles = int(mesh.get_num_triangles(0))
    # The hashed source FBX contract is 14,652 source triangles.  UE 5.8's
    # render-resource metric is deterministically different for some meshes
    # after this importer expands their FBX surface representation (calibrated
    # in the preserved v002 forensic import).  Gate both values explicitly;
    # never relabel UE's render count as the source export count.
    if unreal_render_triangles != spec["unreal_render_triangles"]:
        fail("{} UE render triangles differ from the calibrated import contract: "
             "got {}, expected {} (source FBX triangles remain {})".format(
                 spec["key"], unreal_render_triangles,
                 spec["unreal_render_triangles"], spec["triangles"]))
    slots = tuple(str(slot.material_slot_name) for slot in mesh.static_materials)
    if slots != spec["material_slots"]:
        fail("{} material slots differ: got {}, expected {}".format(
            spec["key"], slots, spec["material_slots"]))
    if not hasattr(mesh_editor, "get_num_uv_channels"):
        fail("UE StaticMeshEditorSubsystem cannot inspect UV channel count")
    uv_channels = int(mesh_editor.get_num_uv_channels(mesh, 0))
    if uv_channels < 2:
        fail("{} lost authored UV1; imported only {} channel(s)".format(
            spec["key"], uv_channels))
    mesh.set_editor_property("light_map_coordinate_index", 1)
    mesh.set_editor_property("light_map_resolution", 128)
    if not unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False):
        fail("cannot save mesh after UV/lightmap verification: {}".format(mesh_path))
    return {
        "source_fbx": SOURCE_PREP_DIR + "/" + spec["fbx"],
        "source_fbx_sha256": sha256(SOURCE_PREP_DIR + "/" + spec["fbx"]),
        "mesh_object_path": mesh_path,
        "dimensions_cm": dimensions,
        "source_triangles": spec["triangles"],
        "unreal_render_triangles": unreal_render_triangles,
        "material_slots": slots,
        "uv_channels": uv_channels,
        "light_map_coordinate_index": 1,
        "light_map_resolution": 128,
        "combined_meshes": True,
        "generated_lightmap_uvs": False,
        "auto_generated_collision": False,
    }


def expression(material, klass, x, y):
    return unreal.MaterialEditingLibrary.create_material_expression(material, klass, x, y)


def build_master(default_textures):
    name = "M_CA_MW_PT_StagePack_PBR_Master_v001"
    master = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MATERIAL_DESTINATION, unreal.Material, unreal.MaterialFactoryNew())
    if master is None:
        fail("could not create StagePack PBR master")
    master.set_editor_property("two_sided", False)
    editing = unreal.MaterialEditingLibrary

    uv0 = expression(master, unreal.MaterialExpressionTextureCoordinate, -1100, 50)
    uv0.set_editor_property("coordinate_index", 0)

    def sample_parameter(name, texture, sampler_type, x, y):
        node = expression(master, unreal.MaterialExpressionTextureSampleParameter2D, x, y)
        node.set_editor_properties({
            "parameter_name": name,
            "texture": texture,
            "sampler_type": sampler_type,
        })
        editing.connect_material_expressions(uv0, "", node, "UVs")
        return node

    base = sample_parameter("BaseColorMap", default_textures["BC"],
                            unreal.MaterialSamplerType.SAMPLERTYPE_COLOR, -840, -180)
    normal = sample_parameter("NormalMap", default_textures["N"],
                              unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL, -840, 80)
    orm = sample_parameter("ORMMap", default_textures["ORM"],
                           unreal.MaterialSamplerType.SAMPLERTYPE_MASKS, -840, 320)
    mask = sample_parameter("WearMaskMap", default_textures["MASK"],
                            unreal.MaterialSamplerType.SAMPLERTYPE_MASKS, -840, 600)

    # The source BC/ORM already contain its approved surface variation.  This
    # is a deliberately restrained runtime seam using raw dust (mask B), not a
    # substitute texture or a fabricated weathering treatment.
    dust = expression(master, unreal.MaterialExpressionComponentMask, -600, 600)
    dust.set_editor_property("b", True)
    editing.connect_material_expressions(mask, "RGB", dust, "")
    dust_strength = expression(master, unreal.MaterialExpressionScalarParameter, -600, 720)
    dust_strength.set_editor_properties({
        "parameter_name": "RawDustStrength", "default_value": 0.0,
    })
    dust_alpha = expression(master, unreal.MaterialExpressionMultiply, -390, 660)
    editing.connect_material_expressions(dust, "", dust_alpha, "A")
    editing.connect_material_expressions(dust_strength, "", dust_alpha, "B")
    dust_tint = expression(master, unreal.MaterialExpressionConstant3Vector, -600, -30)
    dust_tint.set_editor_property("constant", unreal.LinearColor(0.80, 0.80, 0.80, 1.0))
    dusty_base = expression(master, unreal.MaterialExpressionMultiply, -390, -115)
    editing.connect_material_expressions(base, "RGB", dusty_base, "A")
    editing.connect_material_expressions(dust_tint, "", dusty_base, "B")
    mixed_base = expression(master, unreal.MaterialExpressionLinearInterpolate, -150, -115)
    editing.connect_material_expressions(base, "RGB", mixed_base, "A")
    editing.connect_material_expressions(dusty_base, "", mixed_base, "B")
    editing.connect_material_expressions(dust_alpha, "", mixed_base, "Alpha")
    editing.connect_material_property(mixed_base, "", unreal.MaterialProperty.MP_BASE_COLOR)

    editing.connect_material_property(normal, "RGB", unreal.MaterialProperty.MP_NORMAL)
    ao = expression(master, unreal.MaterialExpressionComponentMask, -600, 320)
    ao.set_editor_property("r", True)
    editing.connect_material_expressions(orm, "RGB", ao, "")
    editing.connect_material_property(ao, "", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    roughness = expression(master, unreal.MaterialExpressionComponentMask, -600, 400)
    roughness.set_editor_property("g", True)
    editing.connect_material_expressions(orm, "RGB", roughness, "")
    editing.connect_material_property(roughness, "", unreal.MaterialProperty.MP_ROUGHNESS)
    metallic = expression(master, unreal.MaterialExpressionComponentMask, -600, 480)
    metallic.set_editor_property("b", True)
    editing.connect_material_expressions(orm, "RGB", metallic, "")
    editing.connect_material_property(metallic, "", unreal.MaterialProperty.MP_METALLIC)

    # No emissive node: the delivered StatusGreen and StatusAmber families are
    # intentionally non-emissive, and the opaque InspectionGlass is not a
    # transparent legacy substitute.
    editing.recompile_material(master)
    if not unreal.EditorAssetLibrary.save_loaded_asset(master, only_if_is_dirty=False):
        fail("cannot save StagePack PBR master")
    return master


def build_instance(family, textures, master):
    name = "MI_CA_MW_PT_{}_v001".format(family)
    instance = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MATERIAL_DESTINATION, unreal.MaterialInstanceConstant,
        unreal.MaterialInstanceConstantFactoryNew())
    if instance is None:
        fail("could not create material instance for {}".format(family))
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
    editing.set_material_instance_scalar_parameter_value(
        instance, "RawDustStrength", FAMILY_DUST[family])
    if not unreal.EditorAssetLibrary.save_loaded_asset(instance, only_if_is_dirty=False):
        fail("cannot save material instance for {}".format(family))
    return instance


def bind_mesh_materials(spec, mesh, material_by_slot):
    static_materials = list(mesh.get_editor_property("static_materials"))
    if len(static_materials) != len(spec["material_slots"]):
        fail("{} changed material-slot count before binding".format(spec["key"]))
    for index, (slot, expected_slot) in enumerate(zip(
            static_materials, spec["material_slots"])):
        actual_slot = str(slot.get_editor_property("material_slot_name"))
        if actual_slot != expected_slot:
            fail("{} slot {} drifted before binding: {} != {}".format(
                spec["key"], index, actual_slot, expected_slot))
        material = material_by_slot.get(expected_slot)
        if material is None:
            fail("no material exists for semantic slot {}".format(expected_slot))
        slot.set_editor_property("material_interface", material)
        mesh.set_material(index, material)
    mesh.set_editor_property("static_materials", static_materials)
    if not unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False):
        fail("cannot save material bindings for {}".format(spec["key"]))


with io.open(SOURCE_ASSET_DIR + "/stagepack_manifest.json", "r", encoding="utf-8") as handle:
    stage_manifest = json.load(handle)
with io.open(SOURCE_ASSET_DIR + "/texture_material_manifest.json", "r", encoding="utf-8") as handle:
    texture_manifest = json.load(handle)
with io.open(SOURCE_PREP_DIR + "/runtime_prep_stats.json", "r", encoding="utf-8") as handle:
    runtime_stats = json.load(handle)

preflight(stage_manifest, texture_manifest, runtime_stats)
unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")

source_texture_specs = texture_specs(texture_manifest)
texture_assets = {}
for texture_spec in source_texture_specs:
    texture_assets[texture_spec["asset_name"]] = import_texture(texture_spec)

mesh_assets = {}
mesh_paths = {}
for export_spec in EXPORTS:
    mesh_assets[export_spec["key"]], mesh_paths[export_spec["key"]] = import_mesh(export_spec)

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
mesh_editor = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
if mesh_editor is None:
    fail("StaticMeshEditorSubsystem is unavailable")
mesh_results = {
    spec["key"]: verify_mesh(spec, mesh_assets[spec["key"]], mesh_paths[spec["key"]], mesh_editor)
    for spec in EXPORTS
}

textures_by_family = {family: {} for family in FAMILIES}
for texture_spec in source_texture_specs:
    textures_by_family[texture_spec["family"]][texture_spec["channel"]] = (
        texture_assets[texture_spec["asset_name"]])
for family in FAMILIES:
    if set(textures_by_family[family]) != {"BC", "N", "ORM", "MASK"}:
        fail("incomplete imported PBR family: {}".format(family))

master_material = build_master(textures_by_family["FoundryCharcoal"])
material_by_slot = {}
material_paths = {}
for family in FAMILIES:
    material = build_instance(family, textures_by_family, master_material)
    slot = "CA_MW_{}".format(family)
    material_by_slot[slot] = material
    material_paths[slot] = material.get_path_name()
for export_spec in EXPORTS:
    bind_mesh_materials(export_spec, mesh_assets[export_spec["key"]], material_by_slot)

unreal.EditorAssetLibrary.save_directory(DESTINATION, only_if_is_dirty=False, recursive=True)
receipt = {
    "schema": "lineboss/onefactory/press/s03s06-stagepack-runtimeprep-v001-import/v1",
    "status": "PASS__TEXTURED_STAGEPACK_V001_IMPORTED_AT_RECEIPTED_UNREAL_SCALE",
    "destination": DESTINATION,
    "source_asset": SOURCE_ASSET_DIR,
    "source_runtimeprep": SOURCE_PREP_DIR,
    "source_blend_sha256": runtime_stats["source_blend_sha256"],
    "source_stagepack_manifest_sha256": sha256(
        SOURCE_ASSET_DIR + "/stagepack_manifest.json"),
    "source_texture_manifest_sha256": sha256(
        SOURCE_ASSET_DIR + "/texture_material_manifest.json"),
    "source_runtimeprep_stats_sha256": sha256(
        SOURCE_PREP_DIR + "/runtime_prep_stats.json"),
    "predecessor_v002_forensic_geometry_audit": (
        PROJECT_ROOT + "/Saved/Audits/OneFactory/Press/"
        "S03S06StagePackRuntimePrep_v001/partial_v002_geometry_audit.json"
    ),
    "predecessor_v002_namespace_preserved": (
        "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
        "SharedTrainModules_v002"
    ),
    "modules": mesh_results,
    "textures": {
        name: texture.get_path_name() for name, texture in sorted(texture_assets.items())
    },
    "texture_settings": {
        "BC": "sRGB + TC_DEFAULT",
        "N": "linear + TC_NORMALMAP + OpenGL green flip",
        "ORM": "linear + TC_MASKS",
        "MASK": "linear + TC_MASKS",
    },
    "material_master": master_material.get_path_name(),
    "materials_by_semantic_slot": material_paths,
    "material_parameter_contract": [
        "BaseColorMap", "NormalMap", "ORMMap", "WearMaskMap", "RawDustStrength",
    ],
    "status_lamps_emissive": False,
    "inspection_glass_blend_mode": "opaque",
    "imported_materials_from_fbx": False,
    "imported_textures_from_fbx": False,
    "native_material_closure": True,
    "normal_maps_green_flipped": True,
    "auto_generated_collision": False,
    "authored_lods": "LOD0 only; no LOD1/LOD2 assets shipped",
    "map_loaded": False,
    "map_saved": False,
}
os.makedirs(os.path.dirname(RECEIPT), exist_ok=True)
with io.open(RECEIPT, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")

unreal.log("LINE_BOSS_S03S06_STAGEPACK_RUNTIMEPREP_V001_IMPORT=" +
           json.dumps(receipt, sort_keys=True))
