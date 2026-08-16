"""Audit native HMI material bindings and graph inputs without opening Unreal UI."""

import json
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Developer/Validation/LB_HMI05_UnrealNativeValidation"
MAT_DIR = "/Game/LineBoss/Shared/HMI/IND_HMI_001_V005_UnrealNative/Materials"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/shared_hmi_v005_material_bindings.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)

bindings = []
for actor in actors.get_all_level_actors():
    if not actor.get_actor_label().startswith("LB_HMI05_"):
        continue
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if component is None:
        continue
    material = component.get_material(0)
    bindings.append({
        "actor": actor.get_actor_label(),
        "material": material.get_path_name() if material else None,
    })

graphs = []
for asset_path in unreal.EditorAssetLibrary.list_assets(MAT_DIR, recursive=True, include_folder=False):
    material = unreal.EditorAssetLibrary.load_asset(asset_path)
    if not isinstance(material, unreal.Material):
        continue
    row = {"material": material.get_path_name()}
    for key, prop in (
        ("base_color", unreal.MaterialProperty.MP_BASE_COLOR),
        ("roughness", unreal.MaterialProperty.MP_ROUGHNESS),
        ("metallic", unreal.MaterialProperty.MP_METALLIC),
        ("emissive", unreal.MaterialProperty.MP_EMISSIVE_COLOR),
    ):
        node = unreal.MaterialEditingLibrary.get_material_property_input_node(material, prop)
        row[key] = node.get_path_name() if node else None
    graphs.append(row)

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"bindings": bindings, "graphs": graphs}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_HMI05_MATERIAL_AUDIT_PASS path={OUT}")
