"""Record imported CR01 v038 Unreal static-mesh bounds without modifying assets."""
import json
from pathlib import Path
import unreal

DEST = "/Game/LineBoss/Shared/SupportRobots/LB_CR01/Candidate_v038_ModularRig"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/lb_cr01_unreal_bounds_v038.json"
asset_lib = unreal.EditorAssetLibrary
rows = []
for path in asset_lib.list_assets(DEST, recursive=False, include_folder=False):
    asset = unreal.load_asset(path)
    if not isinstance(asset, unreal.StaticMesh):
        continue
    box = asset.get_bounding_box()
    size = box.max - box.min
    rows.append({
        "asset": asset.get_name(),
        "min_cm": [box.min.x, box.min.y, box.min.z],
        "max_cm": [box.max.x, box.max.y, box.max.z],
        "size_cm": [size.x, size.y, size.z],
    })
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"mesh_count": len(rows), "meshes": rows}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_LB_CR01_V038_BOUNDS_AUDIT {OUT}")
