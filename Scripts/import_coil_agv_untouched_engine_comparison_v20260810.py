"""Import the byte-identical Blender/Unity AGV into an isolated Unreal namespace.

This is an engine/pipeline proof, never a runtime-asset replacement. Geometry,
UVs, normals and the three original 2048 atlases are preserved without Nanite,
decimation, rebaking or generated lightmap UVs.
"""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
STAGE = ROOT / "SourceAssets/Validation/EngineComparison/CoilAGV/Untouched_v20260810"
DEST = "/Game/LineBoss/Developer/Validation/EngineComparison/CoilAGV_Untouched_v20260810"
MESH_NAME = "SM_Cairnwell_CoilAGV_Untouched_v20260810"
PBR_NAME = "M_Cairnwell_CoilAGV_Untouched_PBR_v20260810"
BASE_NAME = "M_Cairnwell_CoilAGV_Untouched_BaseColor_v20260810"
AUDIT = ROOT / "Saved/Audits/EngineComparison/coil_agv_unreal_untouched_import_v20260810.json"
PROTECTED = ROOT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
PROTECTED_SHA = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"

SOURCES = {
    "fbx": (STAGE / "Meshy_AGV_Untouched.fbx", "93CEF19958E2F52D4CC331E74125CBDF49DEC55253C9854C019278C0E93B8482"),
    "base": (STAGE / "Meshy_AGV_Image_0.png", "C2EA1A0B1427030F591CD1FF6104E80290AA68D35A565D4C7360498D620BA74D"),
    "mr": (STAGE / "Meshy_AGV_Image_1.png", "FA579E8422189C93CC443D290E07A2C23D44E4A07800E6335CC2AE17D87AC528"),
    "normal": (STAGE / "Meshy_AGV_Image_2.png", "DB7750C98D98AE1B2A7757320ECAC4827A91E648E51CBF75FE6DA9F690DA3AE4"),
}

EXPECTED_TRIANGLES = 1_984_003
EXPECTED_BOUNDS_SORTED_CM = sorted((145.9682, 190.1947, 57.0366))


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def require_source_hashes():
    rows = {}
    for role, (path, expected) in SOURCES.items():
        if not path.is_file():
            raise RuntimeError(f"Missing untouched comparison source: {path}")
        actual = sha256(path)
        if actual != expected:
            raise RuntimeError(f"Source hash drift for {role}: {actual} != {expected}")
        rows[role] = {"path": str(path), "sha256": actual, "bytes": path.stat().st_size}
    return rows


lib = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
source_rows = require_source_hashes()
protected_before = sha256(PROTECTED)
if protected_before != PROTECTED_SHA:
    raise RuntimeError(f"Protected v438 baseline drift: {protected_before}")
if lib.does_directory_exist(DEST):
    raise RuntimeError(f"Fresh isolated namespace invariant failed: {DEST} already exists")

# Force the deterministic legacy FBX route used by the already-proven high-poly imports.
unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")


def import_mesh(path):
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(path),
        "destination_path": DEST,
        "destination_name": MESH_NAME,
        "automated": True,
        "replace_existing": False,
        "save": True,
    })
    ui = unreal.FbxImportUI()
    ui.set_editor_properties({
        "import_mesh": True,
        "import_as_skeletal": False,
        "import_materials": False,
        "import_textures": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
        "automated_import_should_detect_type": False,
    })
    ui.static_mesh_import_data.set_editor_properties({
        "combine_meshes": True,
        "generate_lightmap_u_vs": False,
        "auto_generate_collision": False,
        "remove_degenerates": False,
        "import_uniform_scale": 100.0,
        "normal_import_method": unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS,
    })
    task.options = ui
    asset_tools.import_asset_tasks([task])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    mesh = lib.load_asset(f"{DEST}/{MESH_NAME}")
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Static mesh import failed: {task.imported_object_paths}")
    return mesh


def import_texture(path, destination_name, srgb, compression):
    folder = f"{DEST}/Textures"
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(path),
        "destination_path": folder,
        "destination_name": destination_name,
        "automated": True,
        "replace_existing": False,
        "save": True,
    })
    asset_tools.import_asset_tasks([task])
    texture = lib.load_asset(f"{folder}/{destination_name}")
    if not isinstance(texture, unreal.Texture2D):
        raise RuntimeError(f"Texture import failed: {destination_name}")
    texture.set_editor_property("srgb", srgb)
    texture.set_editor_property("compression_settings", compression)
    texture.set_editor_property("never_stream", True)
    lib.save_asset(texture.get_path_name(), False)
    if texture.blueprint_get_size_x() != 2048 or texture.blueprint_get_size_y() != 2048:
        raise RuntimeError(f"Unexpected atlas size for {destination_name}")
    return texture


mesh = import_mesh(SOURCES["fbx"][0])
base = import_texture(SOURCES["base"][0], "T_CoilAGV_Untouched_BaseColor_v20260810", True,
                      unreal.TextureCompressionSettings.TC_DEFAULT)
packed_mr = import_texture(SOURCES["mr"][0], "T_CoilAGV_Untouched_MR_v20260810", False,
                           unreal.TextureCompressionSettings.TC_MASKS)
normal = import_texture(SOURCES["normal"][0], "T_CoilAGV_Untouched_Normal_v20260810", False,
                        unreal.TextureCompressionSettings.TC_NORMALMAP)

materials_folder = f"{DEST}/Materials"
pbr = asset_tools.create_asset(PBR_NAME, materials_folder, unreal.Material, unreal.MaterialFactoryNew())
if not pbr:
    raise RuntimeError("PBR material creation failed")
pbr.set_editor_properties({"two_sided": False, "blend_mode": unreal.BlendMode.BLEND_OPAQUE})
base_sample = mel.create_material_expression(pbr, unreal.MaterialExpressionTextureSample, -650, -180)
base_sample.set_editor_property("texture", base)
mel.connect_material_property(base_sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
mr_sample = mel.create_material_expression(pbr, unreal.MaterialExpressionTextureSample, -650, 80)
mr_sample.set_editor_properties({"texture": packed_mr,
                                 "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_MASKS})
mel.connect_material_property(mr_sample, "G", unreal.MaterialProperty.MP_ROUGHNESS)
mel.connect_material_property(mr_sample, "B", unreal.MaterialProperty.MP_METALLIC)
normal_sample = mel.create_material_expression(pbr, unreal.MaterialExpressionTextureSample, -650, 330)
normal_sample.set_editor_properties({"texture": normal,
                                     "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL})
mel.connect_material_property(normal_sample, "RGB", unreal.MaterialProperty.MP_NORMAL)
mel.recompile_material(pbr)
lib.save_asset(pbr.get_path_name(), False)

base_unlit = asset_tools.create_asset(BASE_NAME, materials_folder, unreal.Material, unreal.MaterialFactoryNew())
if not base_unlit:
    raise RuntimeError("Base-colour diagnostic material creation failed")
base_unlit.set_editor_properties({"two_sided": False,
                                  "blend_mode": unreal.BlendMode.BLEND_OPAQUE,
                                  "shading_model": unreal.MaterialShadingModel.MSM_UNLIT})
unlit_sample = mel.create_material_expression(base_unlit, unreal.MaterialExpressionTextureSample, -450, 0)
unlit_sample.set_editor_property("texture", base)
mel.connect_material_property(unlit_sample, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
mel.recompile_material(base_unlit)
lib.save_asset(base_unlit.get_path_name(), False)

mesh.set_material(0, pbr)
nanite = mesh.get_editor_property("nanite_settings")
nanite.enabled = False
mesh.set_editor_property("nanite_settings", nanite)
lib.save_asset(mesh.get_path_name(), False)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

triangles = mesh.get_num_triangles(0)
lod_count = mesh.get_num_lods()
slot_count = len(mesh.get_editor_property("static_materials"))
bounds = mesh.get_bounds().box_extent * 2.0
bounds_cm = [bounds.x, bounds.y, bounds.z]
if triangles != EXPECTED_TRIANGLES:
    raise RuntimeError(f"Triangle drift: {triangles} != {EXPECTED_TRIANGLES}")
if lod_count != 1:
    raise RuntimeError(f"LOD drift: {lod_count} != 1")
if slot_count != 1:
    raise RuntimeError(f"Material slot drift: {slot_count} != 1")
if mesh.get_editor_property("nanite_settings").enabled:
    raise RuntimeError("Nanite must remain disabled for the untouched comparison")
if max(abs(a - e) for a, e in zip(sorted(bounds_cm), EXPECTED_BOUNDS_SORTED_CM)) > 0.35:
    raise RuntimeError(f"Bounds drift: {bounds_cm}")
protected_after = sha256(PROTECTED)
if protected_after != protected_before:
    raise RuntimeError("Protected v438 map changed during isolated AGV import")

AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS_UNTOUCHED_AGV_UNREAL_IMPORT",
    "source": source_rows,
    "destination": DEST,
    "mesh": mesh.get_path_name(),
    "pbr_material": pbr.get_path_name(),
    "base_color_material": base_unlit.get_path_name(),
    "triangles_lod0": triangles,
    "lod_count": lod_count,
    "material_slots": slot_count,
    "bounds_cm": bounds_cm,
    "nanite_enabled": False,
    "texture_contract": {
        "base": {"srgb": True, "size": [2048, 2048]},
        "packed_mr": {"srgb": False, "compression": "TC_MASKS", "green": "roughness", "blue": "metallic"},
        "normal": {"srgb": False, "compression": "TC_NORMALMAP"},
    },
    "topology_changes": 0,
    "meshy_credits_used": 0,
    "protected_v438_sha256": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_UNTOUCHED_AGV_UNREAL_IMPORT_V20260810_PASS")
