"""Calibrate the runtime wrap to a readable cool off-white under factory lighting."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
DEST = "/Game/LineBoss/Runtime/PressShop/WrappedCoil/Controlled_v20260810"
MESH = f"{DEST}/SM_Cairnwell_WrappedCoil_Controlled_v20260810"
BASE = f"{DEST}/Textures/T_Cairnwell_WrappedCoil_BaseColor_v20260810"
MATERIAL_NAME = "M_Cairnwell_WrappedCoil_ControlledPackaging_R2_v20260810"
MATERIAL = f"{DEST}/Materials/{MATERIAL_NAME}"
AUDIT = ROOT / "Saved/Audits/PressTrains/wrapped_coil_controlled_runtime_v20260810_r2.json"
PROTECTED = ROOT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
PROTECTED_SHA = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


if sha256(PROTECTED) != PROTECTED_SHA:
    raise RuntimeError("Protected v438 baseline drift")
lib = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mesh = lib.load_asset(MESH)
base = lib.load_asset(BASE)
if lib.does_asset_exist(MATERIAL):
    raise RuntimeError("Fresh controlled wrapped-coil R2 material already exists")
material = tools.create_asset(
    MATERIAL_NAME, f"{DEST}/Materials", unreal.Material, unreal.MaterialFactoryNew())
if (not isinstance(mesh, unreal.StaticMesh)
        or not isinstance(base, unreal.Texture2D)
        or not isinstance(material, unreal.Material)):
    raise RuntimeError("Controlled wrapped-coil runtime assets are unavailable")
triangles = mesh.get_num_triangles(0)
bounds = mesh.get_bounds().box_extent * 2.0


def vector_near(actual, expected, tolerance):
    return (abs(actual.x - expected.x) <= tolerance
            and abs(actual.y - expected.y) <= tolerance
            and abs(actual.z - expected.z) <= tolerance)


if triangles != 1_906_162 or not vector_near(
        bounds, unreal.Vector(181.0503, 150.0, 178.9497), 0.05):
    raise RuntimeError("Controlled wrapped-coil geometry drift")

material.set_editor_properties({"two_sided": False, "blend_mode": unreal.BlendMode.BLEND_OPAQUE})
sample = mel.create_material_expression(material, unreal.MaterialExpressionTextureSample, -620, -120)
sample.set_editor_property("texture", base)
tint = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -620, 40)
tint.set_editor_property("constant", unreal.LinearColor(0.36, 0.38, 0.40, 1.0))
multiply = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -400, -80)
mel.connect_material_expressions(sample, "RGB", multiply, "A")
mel.connect_material_expressions(tint, "", multiply, "B")
mel.connect_material_property(multiply, "", unreal.MaterialProperty.MP_BASE_COLOR)
for value, y, prop in (
    (0.84, 110, unreal.MaterialProperty.MP_ROUGHNESS),
    (0.00, 220, unreal.MaterialProperty.MP_METALLIC),
    (0.15, 330, unreal.MaterialProperty.MP_SPECULAR),
):
    expression = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -220, y)
    expression.set_editor_property("r", value)
    mel.connect_material_property(expression, "", prop)
mel.recompile_material(material)
lib.save_asset(material.get_path_name(), False)
mesh.set_material(0, material)
lib.save_asset(mesh.get_path_name(), False)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if mesh.get_num_triangles(0) != triangles or not vector_near(
        mesh.get_bounds().box_extent,
        unreal.Vector(90.52515, 75.0, 89.47485), 0.05):
    raise RuntimeError("Material calibration changed wrapped-coil geometry")
if mesh.get_material(0) != material:
    raise RuntimeError("Controlled wrapped-coil R2 material binding failed")
if sha256(PROTECTED) != PROTECTED_SHA:
    raise RuntimeError("Protected v438 map changed")
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS_RUNTIME_CONTROLLED_WRAPPED_COIL_R2",
    "mesh": mesh.get_path_name(),
    "material": material.get_path_name(),
    "base_color": base.get_path_name(),
    "triangles_lod0": triangles,
    "bounds_cm": list(bounds.to_tuple()),
    "wrap_tint_linear": [0.36, 0.38, 0.40],
    "wrap_roughness": 0.84,
    "wrap_metallic": 0.0,
    "wrap_specular": 0.15,
    "lossy_packed_mr_used": False,
    "lossy_normal_used": False,
    "topology_changes": 0,
    "meshy_credits_used": 0,
    "protected_v438_sha256": PROTECTED_SHA,
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_RUNTIME_CONTROLLED_WRAPPED_COIL_V20260810_R2_PASS")
