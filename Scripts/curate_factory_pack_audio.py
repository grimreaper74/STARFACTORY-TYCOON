"""Contain migrated Factory Environment audio in the Line Boss vendor namespace."""

import json
from pathlib import Path

import unreal


SOURCE = "/Game/Audio"
TARGET = "/Game/LineBoss/Vendor/FactoryEnvironment/Audio"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/factory_pack_audio_v001.json"

registry = unreal.AssetRegistryHelpers.get_asset_registry()
registry.scan_paths_synchronous([SOURCE], True)
tools = unreal.AssetToolsHelpers.get_asset_tools()
renames = []
for data in registry.get_assets_by_path(unreal.Name(SOURCE), recursive=True):
    asset = data.get_asset()
    if asset is not None:
        renames.append(unreal.AssetRenameData(asset, TARGET, str(data.asset_name)))
if renames and not tools.rename_assets(renames):
    raise RuntimeError("LINE_BOSS_FACTORY_AUDIO_CURATION_FAIL rename operation failed")

unreal.EditorAssetLibrary.save_directory(TARGET, only_if_is_dirty=False, recursive=True)
records = []
for path in unreal.EditorAssetLibrary.list_assets(TARGET, recursive=True, include_folder=False):
    asset = unreal.load_asset(path)
    record = {"asset": path, "class": asset.get_class().get_name() if asset else "Missing"}
    if isinstance(asset, unreal.SoundWave):
        for prop in ("duration", "num_channels", "sample_rate"):
            try:
                record[prop] = asset.get_editor_property(prop)
            except Exception:
                record[prop] = None
    records.append(record)

if not records:
    raise RuntimeError("LINE_BOSS_FACTORY_AUDIO_CURATION_FAIL no audio assets found")
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"status": "CANDIDATE", "assets": records}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_FACTORY_AUDIO_CURATION_PASS assets={len(records)} output={OUT}")
