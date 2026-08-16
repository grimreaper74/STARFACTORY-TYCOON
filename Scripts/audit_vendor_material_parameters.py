"""Read-only inventory of curated vendor material parameters.

This intentionally writes only an audit JSON under Saved/Audits; it does not
alter source or imported assets.
"""

from __future__ import annotations

import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/Audits/vendor_material_parameters_v001.json"
ASSET_ROOT = "/Game/LineBoss/Vendor/FactoryEnvironment/Materials"


records = []
for asset_path in unreal.EditorAssetLibrary.list_assets(ASSET_ROOT, recursive=True, include_folder=False):
    asset = unreal.load_asset(asset_path)
    if asset is None:
        continue
    record = {
        "asset": asset_path,
        "class": asset.get_class().get_name(),
        "scalar_parameters": [],
        "vector_parameters": [],
        "texture_parameters": [],
    }
    if isinstance(asset, unreal.MaterialInterface):
        for kind, getter, key in (
            ("scalar", unreal.MaterialEditingLibrary.get_scalar_parameter_names, "scalar_parameters"),
            ("vector", unreal.MaterialEditingLibrary.get_vector_parameter_names, "vector_parameters"),
            ("texture", unreal.MaterialEditingLibrary.get_texture_parameter_names, "texture_parameters"),
        ):
            try:
                record[key] = [str(value) for value in getter(asset)]
            except Exception as exc:
                record[key] = [f"ERROR: {exc}"]
        if isinstance(asset, unreal.MaterialInstance):
            try:
                parent = asset.get_editor_property("parent")
                record["parent"] = parent.get_path_name() if parent else None
            except Exception:
                record["parent"] = None
    records.append(record)

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"status": "READ_ONLY_AUDIT_PASS", "records": records}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_VENDOR_MATERIAL_PARAMETER_AUDIT_PASS assets={len(records)} output={OUT}")
