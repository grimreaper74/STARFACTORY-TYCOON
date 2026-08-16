"""Record imported HMI material-slot assignments without opening Unreal."""

from __future__ import annotations

import json
from pathlib import Path

import unreal


DESTINATION = "/Game/LineBoss/Shared/HMI/IND_HMI_001"
OUTPUT = Path(unreal.Paths.project_saved_dir()) / "Audits/shared_hmi_unreal_materials.json"

assets = unreal.EditorAssetLibrary.list_assets(DESTINATION, recursive=True, include_folder=False)
records = []
for path in sorted(assets):
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if not isinstance(asset, unreal.StaticMesh):
        continue
    materials = []
    for index, static_material in enumerate(asset.get_editor_property("static_materials")):
        material = static_material.get_editor_property("material_interface")
        materials.append(
            {
                "slot": index,
                "slot_name": str(static_material.get_editor_property("material_slot_name")),
                "imported_slot_name": str(static_material.get_editor_property("imported_material_slot_name")),
                "material": material.get_path_name() if material is not None else None,
                "class": material.get_class().get_name() if material is not None else None,
            }
        )
    records.append({"mesh": asset.get_path_name(), "material_slots": materials})

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps({"destination": DESTINATION, "meshes": records}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_HMI_MATERIAL_AUDIT_PASS meshes={len(records)} path={OUTPUT}")
