"""Retarget FullHall process fields to a readable candidate-local pale green."""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
MAT_ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Materials"
MAT_NAME = "M_CA_MW_2126_ProcessZonePaleGreen_Unlit_v001"
MAT_PATH = MAT_ROOT + "/" + MAT_NAME
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "process_zones_pale_green_v001_receipt.json"
TAG = unreal.Name("LB.PressShop.2126.ProcessZoneColour.v001")
TARGET_LABELS = (
    "2126 FLOOR | raw-coil receiving bay pale-green field",
    "2126 FLOOR | coil verification buffer bay pale-green field",
    "2126 FLOOR | servo feed bay pale-green field",
    "2126 FLOOR | continuous pale-green press zone",
    "2126 FLOOR | vision palletisation bay pale-green field",
    "2126 OUTBOUND | pale-green magnetic pallet dispatch lane",
)
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()

before = {str(path): digest(path) for path in PROTECTED}
for path, expected in PROTECTED.items():
    if before[str(path)] != expected:
        raise RuntimeError("protected map missing or changed: " + str(path))
if unreal.EditorAssetLibrary.does_asset_exist(MAT_PATH):
    raise RuntimeError("candidate process-zone material already exists")

material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    MAT_NAME, MAT_ROOT, unreal.Material, unreal.MaterialFactoryNew())
if not isinstance(material, unreal.Material):
    raise RuntimeError("could not create process-zone material")
material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
# sRGB target approximately #94ADA0, converted to linear RGB.
colour = unreal.LinearColor(0.296, 0.418, 0.352, 1.0)
constant = unreal.MaterialEditingLibrary.create_material_expression(
    material, unreal.MaterialExpressionConstant3Vector, -220, 0)
constant.set_editor_property("constant", colour)
if not unreal.MaterialEditingLibrary.connect_material_property(
        constant, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR):
    raise RuntimeError("could not connect process-zone colour")
unreal.MaterialEditingLibrary.recompile_material(material)
if not unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False):
    raise RuntimeError("process-zone material did not save")

if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated FullHall candidate")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
if any(TAG in actor.tags for actor in actors.values()):
    raise RuntimeError("process-zone colour pass already tagged")

changed = []
for label in TARGET_LABELS:
    actor = actors.get(label)
    if not isinstance(actor, unreal.StaticMeshActor):
        raise RuntimeError("process zone missing: " + label)
    actor.static_mesh_component.set_material(0, material)
    actor.static_mesh_component.set_editor_property("cast_shadow", False)
    actor.tags = list(actor.tags) + [TAG]
    changed.append(label)

if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("process-zone colour pass did not save")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("protected maps changed during process-zone colour pass")

RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__2126_PROCESS_ZONES_RETARGETED_TO_READABLE_PALE_GREEN",
    "map": MAP,
    "material": material.get_path_name(),
    "srgb_target_hex": "#94ADA0",
    "linear_rgb": [0.296, 0.418, 0.352],
    "changed_actor_count": len(changed),
    "changed": changed,
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2126_PROCESS_ZONE_COLOUR_PASS receipt=" + str(RECEIPT))
unreal.SystemLibrary.quit_editor()
