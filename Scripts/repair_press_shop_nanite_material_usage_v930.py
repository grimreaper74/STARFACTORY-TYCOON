"""Enable Nanite material usage on approved imported Press Shop materials and resave them."""
import unreal
import json
from pathlib import Path

ROOTS = [
    "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v015/TexturedModules/S01",
    "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v015/TexturedModules/Station",
    "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260810_v927/CupTransfer",
    "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v788/S07ConnectedVacuumTool",
    "/Game/LineBoss/Candidates/PressShop/CoilAGV/OriginalTextureSplit_v920",
]

report = []
seen_base_materials = set()
for root in ROOTS:
    for asset_path in unreal.EditorAssetLibrary.list_assets(root, recursive=True, include_folder=False):
        asset = unreal.EditorAssetLibrary.load_asset(asset_path)
        if not isinstance(asset, unreal.MaterialInterface):
            continue
        base = asset if isinstance(asset, unreal.Material) else asset.get_base_material()
        if not base:
            report.append({"material": asset_path, "base": None, "changed": False, "saved": False})
            continue
        base_path = base.get_path_name()
        changed = False
        if base_path not in seen_base_materials:
            seen_base_materials.add(base_path)
            changed = unreal.MaterialEditingLibrary.set_material_usage(base, unreal.MaterialUsage.MATUSAGE_NANITE)
            unreal.MaterialEditingLibrary.recompile_material(base)
            unreal.EditorAssetLibrary.save_loaded_asset(base, only_if_is_dirty=False)
        # The glTF importer creates instances of M_Default. Unreal's warning explicitly
        # requires each instance package to be resaved after the base usage permutation exists.
        saved = unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
        report.append({"material": asset_path, "base": base_path, "base_changed": bool(changed), "saved": bool(saved)})

out = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\Audits\PressTrains\nanite_material_repair_v930.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"roots": ROOTS, "materials": report}, indent=2), encoding="utf-8")
if not report or not all(item["saved"] for item in report):
    raise RuntimeError(f"Nanite material repair incomplete: {out}")
unreal.log(f"LINE_BOSS_NANITE_MATERIAL_REPAIR_V930_PASS count={len(report)} {out}")
