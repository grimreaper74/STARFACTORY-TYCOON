"""Export read-only Surface Forge texture previews for visual selection."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/Audits/SurfaceForgeRobotTexturePreviews/v001"
AUDIT = ROOT / "Saved/Audits/surface_forge_robot_texture_previews_v001.json"
TEXTURES = [
    "/Game/Surface_Forge/Textures/Metal_Paint_Chips/T_Base_Color_Metal_Paint_Chips",
    "/Game/Surface_Forge/Textures/Old_Rust/T_Base_Color_Old_Rust",
    "/Game/Surface_Forge/Textures/Old_Rust/T_Base_Color_Old_Rust1",
]

OUT.mkdir(parents=True, exist_ok=True)
registry = unreal.AssetRegistryHelpers.get_asset_registry()
registry.scan_paths_synchronous(["/Game/Surface_Forge/"], force_rescan=True, ignore_deny_list_scan_filters=True)
records = []
for asset_path in TEXTURES:
    asset = unreal.EditorAssetLibrary.load_asset(asset_path)
    if asset is None:
        records.append({"asset": asset_path, "loaded": False, "exported": False})
        continue
    output = OUT / f"{asset_path.split('/')[-2]}__{asset_path.rsplit('/', 1)[-1]}.png"
    task = unreal.AssetExportTask()
    task.set_editor_property("object", asset)
    task.set_editor_property("filename", str(output))
    task.set_editor_property("automated", True)
    task.set_editor_property("prompt", False)
    task.set_editor_property("replace_identical", True)
    task.set_editor_property("exporter", unreal.TextureExporterPNG())
    exported = bool(unreal.Exporter.run_asset_export_task(task))
    records.append(
        {
            "asset": asset_path,
            "loaded": True,
            "exported": exported,
            "output": str(output),
            "output_exists": output.is_file(),
            "output_bytes": output.stat().st_size if output.is_file() else 0,
            "source_width": asset.blueprint_get_size_x(),
            "source_height": asset.blueprint_get_size_y(),
        }
    )

payload = {
    "$schema": "line-boss/audit/surface-forge-robot-texture-previews-v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY_VENDOR_TEXTURE_PREVIEWS__VISUAL_SELECTION_PENDING__NOT_PROMOTED",
    "records": records,
    "promotion_authorized": False,
}
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_SURFACE_FORGE_TEXTURE_PREVIEW_EXPORT_PASS count={len(records)} audit={AUDIT}")
unreal.SystemLibrary.quit_editor()
