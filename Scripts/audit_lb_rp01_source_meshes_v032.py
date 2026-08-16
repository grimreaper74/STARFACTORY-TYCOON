"""Read-only inventory of RP01 meshes inside the validated CR01 v032 import.

This script deliberately does not promote or modify the v032 candidate.  It
records the live Unreal package names and baked static-mesh bounds so the new
shared mobile-base Blueprint can use verified source assets without guessing
about the FBX axis conversion.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


SOURCE_ROOT = "/Game/LineBoss/Shared/SupportRobots/LB_CR01/Candidate_v032/LOD0"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/lb_rp01_source_meshes_v032.json"

asset_library = unreal.EditorAssetLibrary
rows = []
for asset_path in asset_library.list_assets(SOURCE_ROOT, recursive=False, include_folder=False):
    asset = unreal.load_asset(asset_path)
    if not isinstance(asset, unreal.StaticMesh) or not asset.get_name().startswith("SM_LB_RP01_"):
        continue
    bounds = asset.get_bounding_box()
    centre = (bounds.min + bounds.max) * 0.5
    size = bounds.max - bounds.min
    materials = []
    for slot in asset.get_editor_property("static_materials"):
        material = slot.get_editor_property("material_interface")
        materials.append(material.get_path_name() if material else None)
    rows.append({
        "asset": asset.get_path_name(),
        "name": asset.get_name(),
        "bounds_min_cm": list(bounds.min.to_tuple()),
        "bounds_max_cm": list(bounds.max.to_tuple()),
        "bounds_centre_cm": list(centre.to_tuple()),
        "bounds_size_cm": list(size.to_tuple()),
        "material_paths": materials,
    })

rows.sort(key=lambda row: row["name"])
payload = {
    "$schema": "line-boss/audit/lb-rp01-source-meshes-v032/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY_SOURCE_INVENTORY__V032_REMAINS_CANDIDATE_NOT_PROMOTED",
    "source_root": SOURCE_ROOT,
    "rp01_static_mesh_count": len(rows),
    "meshes": rows,
    "source_assets_modified": False,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_RP01_SOURCE_V032_AUDIT_PASS meshes={len(rows)} audit={OUT}")
unreal.SystemLibrary.quit_editor()
