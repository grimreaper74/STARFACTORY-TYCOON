"""Create a stable release-style AGV paint material from the proven base atlas only."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
DEST = "/Game/LineBoss/Developer/Validation/EngineComparison/CoilAGV_Untouched_v20260810"
TEXTURE = f"{DEST}/Textures/T_CoilAGV_Untouched_BaseColor_v20260810"
FOLDER = f"{DEST}/Materials"
NAME = "M_Cairnwell_CoilAGV_ControlledPaint_v20260810"
ASSET = f"{FOLDER}/{NAME}"
AUDIT = ROOT / "Saved/Audits/EngineComparison/coil_agv_controlled_paint_material_v20260810.json"
PROTECTED = ROOT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
PROTECTED_SHA = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


if sha256(PROTECTED) != PROTECTED_SHA:
    raise RuntimeError("Protected v438 baseline drift")
lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
if lib.does_asset_exist(ASSET):
    raise RuntimeError(f"Fresh controlled-paint asset invariant failed: {ASSET}")
base = lib.load_asset(TEXTURE)
if not isinstance(base, unreal.Texture2D) or not base.get_editor_property("srgb"):
    raise RuntimeError("Proven sRGB base-colour atlas is unavailable")
material = tools.create_asset(NAME, FOLDER, unreal.Material, unreal.MaterialFactoryNew())
if not material:
    raise RuntimeError("Controlled-paint material creation failed")
material.set_editor_properties({"two_sided": False, "blend_mode": unreal.BlendMode.BLEND_OPAQUE})
sample = mel.create_material_expression(material, unreal.MaterialExpressionTextureSample, -520, -100)
sample.set_editor_property("texture", base)
mel.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
roughness = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -260, 110)
roughness.set_editor_property("r", 0.68)
mel.connect_material_property(roughness, "", unreal.MaterialProperty.MP_ROUGHNESS)
metallic = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -260, 230)
metallic.set_editor_property("r", 0.06)
mel.connect_material_property(metallic, "", unreal.MaterialProperty.MP_METALLIC)
specular = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -260, 350)
specular.set_editor_property("r", 0.28)
mel.connect_material_property(specular, "", unreal.MaterialProperty.MP_SPECULAR)
mel.recompile_material(material)
lib.save_asset(material.get_path_name(), False)
if sha256(PROTECTED) != PROTECTED_SHA:
    raise RuntimeError("Protected v438 map changed")
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS_CONTROLLED_AGV_PAINT_MATERIAL",
    "material": material.get_path_name(),
    "base_color": TEXTURE,
    "roughness": 0.68,
    "metallic": 0.06,
    "specular": 0.28,
    "normal_map": None,
    "packed_meshy_mr_used": False,
    "meshy_normal_used": False,
    "geometry_changes": 0,
    "meshy_credits_used": 0,
    "protected_v438_sha256": PROTECTED_SHA,
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_COIL_AGV_CONTROLLED_PAINT_V20260810_PASS")
