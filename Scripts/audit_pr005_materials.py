"""Audit generated PR-005 material graph inputs and mesh assignments."""

import json
from pathlib import Path

import unreal


ROOT = "/Game/LineBoss/Stations/Press/PR005/Candidate_v001"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/pr005_unreal_materials_v001.json"
registry = unreal.AssetRegistryHelpers.get_asset_registry()
assets = registry.get_assets_by_path(ROOT, recursive=True)
records = []
for data in assets:
    asset = data.get_asset()
    if isinstance(asset, unreal.Material):
        node = unreal.MaterialEditingLibrary.get_material_property_input_node(asset, unreal.MaterialProperty.MP_BASE_COLOR)
        value = None
        if node is not None:
            try:
                value = list(node.get_editor_property("constant").to_tuple())
            except Exception as exc:
                value = f"unreadable: {exc}"
        records.append({"type": "material", "asset": asset.get_path_name(), "base_node": node.get_class().get_name() if node else None, "value": value})
    elif isinstance(asset, unreal.StaticMesh):
        records.append({
            "type": "mesh",
            "asset": asset.get_path_name(),
            "slots": [slot.get_editor_property("material_interface").get_path_name() if slot.get_editor_property("material_interface") else None for slot in asset.get_editor_property("static_materials")],
        })

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(records, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR005_MATERIAL_AUDIT_PASS records={len(records)} path={OUT}")
