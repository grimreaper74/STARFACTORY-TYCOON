"""Contain newly migrated Factory Environment logistics assets."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


SOURCE_ROOTS = ("/Game/Meshes", "/Game/Materials", "/Game/Textures")
TARGET_ROOT = "/Game/LineBoss/Vendor/FactoryEnvironment/Logistics"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/factory_pack_logistics_migration_v001.json"

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

if not renames:
    raise RuntimeError("No newly migrated logistics assets found in staging roots")
if not asset_tools.rename_assets(renames):
    raise RuntimeError("Factory logistics containment rename failed")

unreal.EditorAssetLibrary.save_directory(TARGET_ROOT, only_if_is_dirty=False, recursive=True)
target_assets = list(unreal.EditorAssetLibrary.list_assets(
    TARGET_ROOT, recursive=True, include_folder=False))
required_tokens = (
    "SM_ForkLift", "SM_PalletCart", "SM_PlasticPallet01", "SM_AssemblyLineCrate01")
missing = [token for token in required_tokens
           if not any(token in str(asset) for asset in target_assets)]
if missing:
    raise RuntimeError(f"Contained logistics shortlist missing: {missing}")

payload = {
    "$schema": "line-boss/audit/factory-pack-logistics-migration-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "LICENSED_LOGISTICS_SHORTLIST_CONTAINED__ISOLATED_VISUAL_GATE_REQUIRED__NOT_PROMOTED",
    "source_pack": "Factory Environment Collection",
    "source_asset_count": len(source_assets),
    "curated_asset_count": len(target_assets),
    "target_root": TARGET_ROOT,
    "requested_hero_exclusions": ["custom machinery", "coils", "cranes", "robots", "HMI"],
    "source_packages": source_assets,
    "target_assets": [str(asset) for asset in target_assets],
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(
    "LINE_BOSS_FACTORY_LOGISTICS_CURATION_PASS "
    f"source={len(source_assets)} curated={len(target_assets)} target={TARGET_ROOT}"
)
unreal.SystemLibrary.quit_editor()

