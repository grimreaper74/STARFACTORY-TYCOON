"""Disable Nanite only on the two full-detail textured Coil AGV meshes."""
import unreal
import json
from pathlib import Path

ROOT = "/Game/LineBoss/Candidates/PressShop/CoilAGV/OriginalTextureSplit_v920"
report = []
for path in unreal.EditorAssetLibrary.list_assets(ROOT, recursive=True, include_folder=False):
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if not isinstance(asset, unreal.StaticMesh):
        continue
    settings = asset.get_editor_property("nanite_settings")
    was_enabled = bool(settings.enabled)
    settings.enabled = False
    asset.set_editor_property("nanite_settings", settings)
    asset.modify()
    saved = unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
    report.append({"mesh": path, "was_enabled": was_enabled, "nanite_enabled": bool(asset.get_editor_property("nanite_settings").enabled), "saved": bool(saved)})

out = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\Audits\PressTrains\coil_agv_nanite_disabled_v932.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"meshes": report}, indent=2), encoding="utf-8")
if len(report) != 2 or not all(item["saved"] and not item["nanite_enabled"] for item in report):
    raise RuntimeError(f"AGV Nanite test failed: {out}")
unreal.log(f"LINE_BOSS_COIL_AGV_NANITE_DISABLED_V932_PASS {out}")
