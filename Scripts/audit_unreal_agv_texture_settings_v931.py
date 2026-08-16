import unreal
import json
from pathlib import Path

ROOTS = [
    "/Game/LineBoss/Candidates/PressShop/CoilAGV/OriginalTextureSplit_v920",
    "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v015/TexturedModules/Station",
]
items = []
for root in ROOTS:
    for path in unreal.EditorAssetLibrary.list_assets(root, recursive=True, include_folder=False):
        asset = unreal.EditorAssetLibrary.load_asset(path)
        if isinstance(asset, unreal.Texture2D):
            items.append({
                "path": path,
                "srgb": bool(asset.get_editor_property("srgb")),
                "compression": str(asset.get_editor_property("compression_settings")),
                "lod_group": str(asset.get_editor_property("lod_group")),
                "size_x": asset.blueprint_get_size_x(),
                "size_y": asset.blueprint_get_size_y(),
            })
out = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\Audits\PressTrains\unreal_agv_texture_settings_v931.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"textures": items}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_AGV_TEXTURE_SETTINGS_V931 count={len(items)} {out}")
