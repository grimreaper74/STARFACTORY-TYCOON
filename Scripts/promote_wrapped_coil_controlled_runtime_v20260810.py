"""Promote the validated wrapped coil with stable, non-clipping runtime materials."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import unreal


ROOT = Path(unreal.Paths.project_dir()).resolve()
SOURCE_ROOT = "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004/Inbound"
SOURCE_MESH = f"{SOURCE_ROOT}/SM_CA_MW_WrappedCoil_Repaired_v003"
SOURCE_BASE = f"{SOURCE_ROOT}/T_CA_MW_WrappedCoil_BaseColor_v003"
DEST = "/Game/LineBoss/Runtime/PressShop/WrappedCoil/Controlled_v20260810"
MESH_NAME = "SM_Cairnwell_WrappedCoil_Controlled_v20260810"
BASE_NAME = "T_Cairnwell_WrappedCoil_BaseColor_v20260810"
WRAP_MATERIAL_NAME = "M_Cairnwell_WrappedCoil_ControlledPackaging_v20260810"
CORE_MATERIAL_NAME = "M_Cairnwell_WrappedCoil_StructuralCore_v20260810"
AUDIT = ROOT / "Saved/Audits/PressTrains/wrapped_coil_controlled_runtime_v20260810.json"
PROTECTED = ROOT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
PROTECTED_SHA = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def constant(material, value, y, prop):
    expression = mel.create_material_expression(
        material, unreal.MaterialExpressionConstant, -220, y)
    expression.set_editor_property("r", value)
    mel.connect_material_property(expression, "", prop)


lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
if sha256(PROTECTED) != PROTECTED_SHA:
    raise RuntimeError("Protected v438 baseline drift")
if lib.does_directory_exist(DEST):
    raise RuntimeError(f"Fresh runtime namespace invariant failed: {DEST}")

source_mesh = lib.load_asset(SOURCE_MESH)
source_base = lib.load_asset(SOURCE_BASE)
if not isinstance(source_mesh, unreal.StaticMesh) or not isinstance(source_base, unreal.Texture2D):
    raise RuntimeError("Validated wrapped-coil source assets are unavailable")

source_triangles = source_mesh.get_num_triangles(0)
source_lods = source_mesh.get_num_lods()
source_bounds = source_mesh.get_bounds().box_extent * 2.0
runtime_mesh = lib.duplicate_asset(SOURCE_MESH, f"{DEST}/{MESH_NAME}")
runtime_base = lib.duplicate_asset(SOURCE_BASE, f"{DEST}/Textures/{BASE_NAME}")
if not isinstance(runtime_mesh, unreal.StaticMesh) or not isinstance(runtime_base, unreal.Texture2D):
    raise RuntimeError("Wrapped-coil runtime duplication failed")
runtime_base.set_editor_properties({
    "srgb": True,
    "compression_settings": unreal.TextureCompressionSettings.TC_DEFAULT,
    "never_stream": False,
})
lib.save_asset(runtime_base.get_path_name(), False)

wrap_material = tools.create_asset(
    WRAP_MATERIAL_NAME, f"{DEST}/Materials", unreal.Material, unreal.MaterialFactoryNew())
core_material = tools.create_asset(
    CORE_MATERIAL_NAME, f"{DEST}/Materials", unreal.Material, unreal.MaterialFactoryNew())
if not wrap_material or not core_material:
    raise RuntimeError("Controlled wrapped-coil material creation failed")

wrap_material.set_editor_properties({"two_sided": False, "blend_mode": unreal.BlendMode.BLEND_OPAQUE})
sample = mel.create_material_expression(wrap_material, unreal.MaterialExpressionTextureSample, -620, -120)
sample.set_editor_property("texture", runtime_base)
tint = mel.create_material_expression(wrap_material, unreal.MaterialExpressionConstant3Vector, -620, 40)
tint.set_editor_property("constant", unreal.LinearColor(0.62, 0.64, 0.66, 1.0))
multiply = mel.create_material_expression(wrap_material, unreal.MaterialExpressionMultiply, -400, -80)
mel.connect_material_expressions(sample, "RGB", multiply, "A")
mel.connect_material_expressions(tint, "", multiply, "B")
mel.connect_material_property(multiply, "", unreal.MaterialProperty.MP_BASE_COLOR)
constant(wrap_material, 0.82, 110, unreal.MaterialProperty.MP_ROUGHNESS)
constant(wrap_material, 0.00, 220, unreal.MaterialProperty.MP_METALLIC)
constant(wrap_material, 0.18, 330, unreal.MaterialProperty.MP_SPECULAR)
mel.recompile_material(wrap_material)
lib.save_asset(wrap_material.get_path_name(), False)

core_material.set_editor_properties({"two_sided": False, "blend_mode": unreal.BlendMode.BLEND_OPAQUE})
core_colour = mel.create_material_expression(core_material, unreal.MaterialExpressionConstant3Vector, -360, -50)
core_colour.set_editor_property("constant", unreal.LinearColor(0.055, 0.065, 0.075, 1.0))
mel.connect_material_property(core_colour, "", unreal.MaterialProperty.MP_BASE_COLOR)
constant(core_material, 0.68, 100, unreal.MaterialProperty.MP_ROUGHNESS)
constant(core_material, 0.15, 210, unreal.MaterialProperty.MP_METALLIC)
constant(core_material, 0.22, 320, unreal.MaterialProperty.MP_SPECULAR)
mel.recompile_material(core_material)
lib.save_asset(core_material.get_path_name(), False)

if len(runtime_mesh.get_editor_property("static_materials")) != 2:
    raise RuntimeError("Wrapped-coil body/core material-slot invariant failed")
runtime_mesh.set_material(0, wrap_material)
runtime_mesh.set_material(1, core_material)
nanite = runtime_mesh.get_editor_property("nanite_settings")
nanite.enabled = False
runtime_mesh.set_editor_property("nanite_settings", nanite)
lib.save_asset(runtime_mesh.get_path_name(), False)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

runtime_bounds = runtime_mesh.get_bounds().box_extent * 2.0
if runtime_mesh.get_num_triangles(0) != source_triangles or runtime_mesh.get_num_lods() != source_lods:
    raise RuntimeError("Wrapped-coil runtime topology drift")
for expected, actual in zip(source_bounds.to_tuple(), runtime_bounds.to_tuple()):
    if abs(expected - actual) > 0.001:
        raise RuntimeError("Wrapped-coil runtime bounds drift")
if runtime_mesh.get_material(0) != wrap_material or runtime_mesh.get_material(1) != core_material:
    raise RuntimeError("Wrapped-coil controlled-material binding failed")
if sha256(PROTECTED) != PROTECTED_SHA:
    raise RuntimeError("Protected v438 map changed")

AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS_RUNTIME_CONTROLLED_WRAPPED_COIL",
    "source_mesh": SOURCE_MESH,
    "runtime_mesh": runtime_mesh.get_path_name(),
    "runtime_base_color": runtime_base.get_path_name(),
    "runtime_materials": [wrap_material.get_path_name(), core_material.get_path_name()],
    "triangles_lod0": source_triangles,
    "lod_count": source_lods,
    "bounds_cm": list(runtime_bounds.to_tuple()),
    "nanite_enabled": False,
    "wrap_tint_linear": [0.62, 0.64, 0.66],
    "wrap_roughness": 0.82,
    "wrap_metallic": 0.0,
    "wrap_specular": 0.18,
    "meshy_packed_mr_used": False,
    "meshy_normal_used": False,
    "topology_changes": 0,
    "meshy_credits_used": 0,
    "protected_v438_sha256": PROTECTED_SHA,
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_RUNTIME_CONTROLLED_WRAPPED_COIL_V20260810_PASS")
