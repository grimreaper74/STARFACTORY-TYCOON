"""Create an isolated compact-layout v003 candidate; never touch v438 or v002."""
import hashlib
import json
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Maps/LB_PressShop_2126_Steam_v003"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
V002 = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2126_v003_map_create.json"


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


if unreal.EditorAssetLibrary.does_asset_exist(MAP):
    raise RuntimeError("v003 map already exists; refusing to overwrite a candidate")
if not PROTECTED.is_file() or not V002.is_file():
    raise RuntimeError("Required evidence map missing")
protected_before, v002_before = digest(PROTECTED), digest(V002)
if not unreal.EditorLevelLibrary.new_level(MAP):
    raise RuntimeError("Could not create isolated v003 candidate")
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("Could not save v003 candidate")
protected_after, v002_after = digest(PROTECTED), digest(V002)
if protected_before != protected_after or v002_before != v002_after:
    raise RuntimeError("Protected evidence map changed while v003 was created")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__ISOLATED_COMPACT_V003_CANDIDATE_CREATED",
    "map": MAP,
    "v002_untouched": True,
    "v002_sha256_before": v002_before,
    "v002_sha256_after": v002_after,
    "protected_v438_sha256_before": protected_before,
    "protected_v438_sha256_after": protected_after,
}, indent=2), encoding="utf-8")
unreal.log("PRESSSHOP_2126_V003_MAP_CREATE_PASS")
