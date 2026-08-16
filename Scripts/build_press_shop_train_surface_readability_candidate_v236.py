"""Create v236 from retained v235 with calibrated readable charcoal train skins."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v235"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v236"
MAT_DIR = "/Game/LineBoss/Candidates/PressTrains/Shared/Materials_v236"
MAT_NAME = "M_CA_MW_PT_ReadableGraphiteCharcoal_v236"
SOURCE_MATERIAL = "/Game/LineBoss/Candidates/PressTrains/Shared/Materials_v230/M_CA_MW_PT_ReadableFoundryCharcoal_v230.M_CA_MW_PT_ReadableFoundryCharcoal_v230"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_train_surface_readability_build_v236.json"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v235.umap"

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
mel = unreal.MaterialEditingLibrary


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved candidate {MAP}")
material_path = f"{MAT_DIR}/{MAT_NAME}"
if library.does_asset_exist(material_path):
    raise RuntimeError(f"refusing to overwrite preserved material {material_path}")
parent_hash_before = sha256(BASE_FILE)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP} from {BASE}")

material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    MAT_NAME, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
if material is None:
    raise RuntimeError("could not create v236 train material")
base = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -480, -100)
base.set_editor_property("constant", unreal.LinearColor(0.14, 0.16, 0.18, 1.0))
mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
for value, target, y_value in (
        (0.28, unreal.MaterialProperty.MP_METALLIC, 40),
        (0.56, unreal.MaterialProperty.MP_ROUGHNESS, 150),
        (0.30, unreal.MaterialProperty.MP_SPECULAR, 260)):
    node = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -480, y_value)
    node.set_editor_property("r", value)
    mel.connect_material_property(node, "", target)
compile_errors = [str(value) for value in mel.recompile_material(material)]
library.save_loaded_asset(material, only_if_is_dirty=False)

overrides = []
per_train = {key: 0 for key in "ABCD"}
failures = []
for actor in actors_api.get_all_level_actors():
    tags = {str(tag) for tag in actor.tags}
    train_tag = next((tag for tag in tags if tag.startswith("LB.PressTrain.Installed.TRAIN_")), None)
    if train_tag is None:
        continue
    train_id = train_tag.rsplit("_", 1)[-1]
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component is None or component.static_mesh is None:
        continue
    for slot_index in range(component.get_num_materials()):
        current = component.get_material(slot_index)
        if current is not None and current.get_path_name() == SOURCE_MATERIAL:
            component.set_material(slot_index, material)
            overrides.append({"actor": actor.get_actor_label(), "slot": slot_index, "train": train_id})
            if train_id in per_train:
                per_train[train_id] += 1

if compile_errors:
    failures.append(f"material compile errors: {compile_errors}")
if len(overrides) != 489:
    failures.append(f"expected 489 inherited v230 charcoal slots, changed {len(overrides)}")
if any(count <= 0 for count in per_train.values()):
    failures.append(f"not all four trains received overrides: {per_train}")
if not levels.save_current_level():
    failures.append("could not save v236")
parent_hash_after = sha256(BASE_FILE)
if parent_hash_after != parent_hash_before:
    failures.append("protected v235 parent changed")
map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v236.umap"
payload = {
    "$schema": "cairnwell/audit/press-shop-train-surface-readability-build-v236/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__FOUR_INSTALLED_TRAINS_RECEIVE_CALIBRATED_GRAPHITE_CHARCOAL__FRESH_VISUAL_RUNTIME_AND_FULL_REGRESSION_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "base": BASE,
    "map": MAP,
    "parent_hash_before": parent_hash_before,
    "parent_hash_after": parent_hash_after,
    "map_hash": sha256(map_file) if map_file.exists() else None,
    "source_material": SOURCE_MATERIAL,
    "override_material": material.get_path_name(),
    "override_count": len(overrides),
    "override_count_by_train": per_train,
    "colour_linear": [0.14, 0.16, 0.18],
    "metallic": 0.28,
    "roughness": 0.56,
    "specular": 0.30,
    "geometry_transform_tooling_accent_authority_machine_changes": 0,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
