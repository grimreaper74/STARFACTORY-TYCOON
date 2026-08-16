"""Audit UV availability before assigning tiled PBR materials to PR-004."""

from __future__ import annotations

import json
from pathlib import Path

import unreal


ROOT = "/Game/LineBoss/Stations/Press/PR004/Candidate_v002"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/pr004_candidate_uv_audit_v001.json"
registry = unreal.AssetRegistryHelpers.get_asset_registry()
assets = registry.get_assets_by_path(ROOT, recursive=True)
records = []
for data in assets:
    asset = data.get_asset()
    if not isinstance(asset, unreal.StaticMesh):
        continue
    lods = asset.get_num_lods()
    records.append({
        "asset": asset.get_path_name(),
        "lods": lods,
        "uv_channels_per_lod": [asset.get_num_tex_coords(index) for index in range(lods)],
        "material_slots": [slot.get_editor_property("material_slot_name").to_string() for slot in asset.get_editor_property("static_materials")],
    })

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "status": "PASS" if records and all(r["uv_channels_per_lod"][0] > 0 for r in records) else "FAIL",
    "root": ROOT,
    "static_mesh_count": len(records),
    "records": records,
}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_UV_AUDIT={OUT}")
