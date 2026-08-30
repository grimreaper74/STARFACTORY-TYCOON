"""Create an empty, isolated v002 Press Shop candidate map.

This is deliberately a new level.  It never opens or writes the protected v438
authority map, and it leaves the earlier v001 candidate available for history.
"""

import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps/LB_PressShop_2126_Steam_v002"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v002_map_create.json"


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


if not PROTECTED.is_file():
    raise RuntimeError("Protected v438 map is missing")
if unreal.EditorAssetLibrary.does_asset_exist(MAP):
    raise RuntimeError("v002 map already exists; refusing to overwrite a candidate")

before = digest(PROTECTED)
if not unreal.EditorLevelLibrary.new_level(MAP):
    raise RuntimeError("Could not create v002 candidate level")
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save v002 candidate level")
after = digest(PROTECTED)
if before != after:
    raise RuntimeError("Protected v438 map changed while v002 was created")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__ISOLATED_V002_CANDIDATE_MAP_CREATED",
    "map": MAP,
    "previous_v001_candidate_modified": False,
    "protected_v438_sha256_before": before,
    "protected_v438_sha256_after": after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V002_MAP_CREATE_PASS")
