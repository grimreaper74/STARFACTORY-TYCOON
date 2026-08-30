"""Clone the first sprite proof before applying the overhead visual master."""
import hashlib
import json
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = "/Game/LineBoss/Candidates/PressShop/PressShopFactorio2p5D_Full_v002_SpriteArt/Maps/LB_PressShop_Factorio2p5D_Full_v002_SpriteArt"
TARGET = "/Game/LineBoss/Candidates/PressShop/PressShopFactorio2p5D_Full_v003_OverheadSprites/Maps/LB_PressShop_Factorio2p5D_Full_v003_OverheadSprites"
SOURCE_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShopFactorio2p5D_Full_v002_SpriteArt" / "Maps" / "LB_PressShop_Factorio2p5D_Full_v002_SpriteArt.umap"
TARGET_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShopFactorio2p5D_Full_v003_OverheadSprites" / "Maps" / "LB_PressShop_Factorio2p5D_Full_v003_OverheadSprites.umap"
PROTECTED = {
    "v438": PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap",
    "steam_v002": PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap",
}
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_factorio_2p5d_full_v003_overhead_sprite_clone.json"

def fail(message):
    raise RuntimeError("PRESSSHOP_2P5D_OVERHEAD_SPRITE_CLONE_FAIL: " + message)

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

if not SOURCE_FILE.is_file() or any(not path.is_file() for path in PROTECTED.values()):
    fail("source or protected evidence map is missing")
if TARGET_FILE.exists() or unreal.EditorAssetLibrary.does_asset_exist(TARGET):
    fail("v003 overhead target already exists; refusing overwrite")
before = {"source_v002": sha256(SOURCE_FILE)}
before.update({name: sha256(path) for name, path in PROTECTED.items()})
if not unreal.EditorAssetLibrary.duplicate_asset(SOURCE, TARGET):
    fail("Unreal did not duplicate the v002 sprite proof")
target = unreal.load_asset(TARGET)
if target is None or not unreal.EditorAssetLibrary.save_loaded_asset(target, only_if_is_dirty=False):
    fail("cloned v003 map could not be saved")
if not TARGET_FILE.is_file():
    fail("target map was not written")
after = {"source_v002": sha256(SOURCE_FILE)}
after.update({name: sha256(path) for name, path in PROTECTED.items()})
if before != after:
    fail("source proof or protected evidence changed during v003 clone")
report = {
    "status": "PASS__V003_OVERHEAD_SPRITE_CANDIDATE_CLONED_ONLY__RESTART_REQUIRED_BEFORE_MATERIAL_SWAP",
    "source": SOURCE, "target": TARGET,
    "source_hash_before": before["source_v002"], "source_hash_after": after["source_v002"],
    "target_hash": sha256(TARGET_FILE),
    "protected_before": before, "protected_after": after,
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2P5D_OVERHEAD_SPRITE_CLONE_PASS=" + TARGET)

