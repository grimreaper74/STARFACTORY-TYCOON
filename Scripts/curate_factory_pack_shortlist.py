"""Move migrated Factory Environment assets into a contained vendor namespace."""

import json
from pathlib import Path

import unreal


SOURCE_ROOTS = ("/Game/Meshes", "/Game/Materials", "/Game/Textures")
TARGET_ROOT = "/Game/LineBoss/Vendor/FactoryEnvironment"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/factory_pack_migration_v001.json"

registry = unreal.AssetRegistryHelpers.get_asset_registry()
registry.scan_paths_synchronous(list(SOURCE_ROOTS), True)
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
renames = []
source_assets = []

for source_root in SOURCE_ROOTS:
    for data in registry.get_assets_by_path(unreal.Name(source_root), recursive=True):
        asset = data.get_asset()
        if asset is None:
            continue
        package_path = str(data.package_path)
        relative_path = package_path[len("/Game/"):]
        target_path = f"{TARGET_ROOT}/{relative_path}"
        renames.append(unreal.AssetRenameData(asset, target_path, str(data.asset_name)))
        source_assets.append(str(data.package_name))

if renames and not asset_tools.rename_assets(renames):
    raise RuntimeError("LINE_BOSS_FACTORY_PACK_CURATION_FAIL rename operation failed")

unreal.EditorAssetLibrary.save_directory(TARGET_ROOT, only_if_is_dirty=False, recursive=True)
target_assets = [
    str(value)
    for value in unreal.EditorAssetLibrary.list_assets(TARGET_ROOT, recursive=True, include_folder=False)
]
if not target_assets:
    raise RuntimeError("LINE_BOSS_FACTORY_PACK_CURATION_FAIL no curated assets found")
result = {
    "status": "PASS",
    "source_asset_count": len(source_assets),
    "curated_asset_count": len(target_assets),
    "target_root": TARGET_ROOT,
    "source_packages": source_assets,
    "target_assets": target_assets,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log(
    "LINE_BOSS_FACTORY_PACK_CURATION_PASS "
    f"source={len(source_assets)} curated={len(target_assets)} target={TARGET_ROOT}"
)
