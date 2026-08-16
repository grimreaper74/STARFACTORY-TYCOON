"""Promote the proven untouched AGV plus stable base-atlas paint into runtime content."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
SOURCE_ROOT = "/Game/LineBoss/Developer/Validation/EngineComparison/CoilAGV_Untouched_v20260810"
SOURCE_MESH = f"{SOURCE_ROOT}/SM_Cairnwell_CoilAGV_Untouched_v20260810"
SOURCE_BASE = f"{SOURCE_ROOT}/Textures/T_CoilAGV_Untouched_BaseColor_v20260810"
DEST = "/Game/LineBoss/Runtime/PressShop/CoilAGV/UntouchedControlled_v20260810"
MESH_NAME = "SM_Cairnwell_CoilAGV_UntouchedControlled_v20260810"
TEXTURE_NAME = "T_Cairnwell_CoilAGV_BaseColor_v20260810"
MATERIAL_NAME = "M_Cairnwell_CoilAGV_ControlledPaint_v20260810"
AUDIT = ROOT / "Saved/Audits/PressTrains/coil_agv_untouched_controlled_runtime_v20260810.json"
PROTECTED = ROOT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
PROTECTED_SHA = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


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
    raise RuntimeError("Proven untouched comparison assets are unavailable")

runtime_mesh = lib.duplicate_asset(SOURCE_MESH, f"{DEST}/{MESH_NAME}")
runtime_base = lib.duplicate_asset(SOURCE_BASE, f"{DEST}/Textures/{TEXTURE_NAME}")
if not isinstance(runtime_mesh, unreal.StaticMesh) or not isinstance(runtime_base, unreal.Texture2D):
    raise RuntimeError("Runtime duplication failed")
runtime_base.set_editor_properties({"srgb": True,
                                    "compression_settings": unreal.TextureCompressionSettings.TC_DEFAULT,
                                    "never_stream": False})
lib.save_asset(runtime_base.get_path_name(), False)

material = tools.create_asset(MATERIAL_NAME, f"{DEST}/Materials",
                              unreal.Material, unreal.MaterialFactoryNew())
if not material:
    raise RuntimeError("Runtime controlled-paint material creation failed")
material.set_editor_properties({"two_sided": False, "blend_mode": unreal.BlendMode.BLEND_OPAQUE})
sample = mel.create_material_expression(material, unreal.MaterialExpressionTextureSample, -520, -100)
sample.set_editor_property("texture", runtime_base)
mel.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
for value, y, prop in [
    (0.68, 110, unreal.MaterialProperty.MP_ROUGHNESS),
    (0.06, 230, unreal.MaterialProperty.MP_METALLIC),
    (0.28, 350, unreal.MaterialProperty.MP_SPECULAR),
]:
    expression = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -260, y)
    expression.set_editor_property("r", value)
    mel.connect_material_property(expression, "", prop)
mel.recompile_material(material)
lib.save_asset(material.get_path_name(), False)

runtime_mesh.set_material(0, material)
nanite = runtime_mesh.get_editor_property("nanite_settings")
nanite.enabled = False
runtime_mesh.set_editor_property("nanite_settings", nanite)
lib.save_asset(runtime_mesh.get_path_name(), False)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

bounds = runtime_mesh.get_bounds().box_extent * 2
if runtime_mesh.get_num_triangles(0) != 1_984_003 or runtime_mesh.get_num_lods() != 1:
    raise RuntimeError("Runtime mesh topology drift")
if len(runtime_mesh.get_editor_property("static_materials")) != 1:
    raise RuntimeError("Runtime mesh material slot drift")
if runtime_mesh.get_material(0) != material:
    raise RuntimeError("Runtime controlled-paint binding failed")
if sha256(PROTECTED) != PROTECTED_SHA:
    raise RuntimeError("Protected v438 map changed")
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS_RUNTIME_UNTOUCHED_CONTROLLED_AGV",
    "source_mesh": SOURCE_MESH,
    "runtime_mesh": runtime_mesh.get_path_name(),
    "runtime_material": material.get_path_name(),
    "runtime_base_color": runtime_base.get_path_name(),
    "triangles_lod0": runtime_mesh.get_num_triangles(0),
    "lod_count": runtime_mesh.get_num_lods(),
    "bounds_cm": list(bounds.to_tuple()),
    "nanite_enabled": False,
    "roughness": 0.68, "metallic": 0.06, "specular": 0.28,
    "normal_map": None, "meshy_packed_mr_used": False,
    "topology_changes": 0, "meshy_credits_used": 0,
    "protected_v438_sha256": PROTECTED_SHA,
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_RUNTIME_UNTOUCHED_CONTROLLED_AGV_V20260810_PASS")
