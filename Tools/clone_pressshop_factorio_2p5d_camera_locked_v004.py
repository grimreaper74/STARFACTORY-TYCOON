"""Clone the rejected v003 mount before correcting its actual camera and sprite basis."""
import hashlib
import json
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = "/Game/LineBoss/Candidates/PressShop/PressShopFactorio2p5D_Full_v003_OverheadSprites/Maps/LB_PressShop_Factorio2p5D_Full_v003_OverheadSprites"
TARGET = "/Game/LineBoss/Candidates/PressShop/PressShopFactorio2p5D_Full_v004_CameraLockedSprites/Maps/LB_PressShop_Factorio2p5D_Full_v004_CameraLockedSprites"
SOURCE_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShopFactorio2p5D_Full_v003_OverheadSprites" / "Maps" / "LB_PressShop_Factorio2p5D_Full_v003_OverheadSprites.umap"
TARGET_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShopFactorio2p5D_Full_v004_CameraLockedSprites" / "Maps" / "LB_PressShop_Factorio2p5D_Full_v004_CameraLockedSprites.umap"
PROTECTED = {
    "v438": PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap",
    "steam_v002": PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap",
}
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_factorio_2p5d_full_v004_camera_locked_clone.json"

def fail(message):
    raise RuntimeError("PRESSSHOP_2P5D_CAMERA_LOCKED_CLONE_FAIL: " + message)

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

if not SOURCE_FILE.is_file() or any(not path.is_file() for path in PROTECTED.values()):
    fail("source or protected map is missing")
if TARGET_FILE.exists() or unreal.EditorAssetLibrary.does_asset_exist(TARGET):
    fail("v004 camera-locked target already exists")
before = {"source_v003": sha256(SOURCE_FILE)}
before.update({name: sha256(path) for name, path in PROTECTED.items()})
if not unreal.EditorAssetLibrary.duplicate_asset(SOURCE, TARGET):
    fail("Unreal did not duplicate rejected v003 candidate")
target = unreal.load_asset(TARGET)
if target is None or not unreal.EditorAssetLibrary.save_loaded_asset(target, only_if_is_dirty=False):
    fail("target candidate could not be saved")
if not TARGET_FILE.is_file():
    fail("target map was not written")
after = {"source_v003": sha256(SOURCE_FILE)}
after.update({name: sha256(path) for name, path in PROTECTED.items()})
if before != after:
    fail("source candidate or protected evidence changed during clone")
report = {
    "status": "PASS__V004_CAMERA_LOCKED_SPRITE_CANDIDATE_CLONED_ONLY__RESTART_REQUIRED",
    "source": SOURCE, "target": TARGET,
    "source_hash_before": before["source_v003"], "source_hash_after": after["source_v003"],
    "target_hash": sha256(TARGET_FILE), "evidence_before": before, "evidence_after": after,
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2P5D_CAMERA_LOCKED_CLONE_PASS=" + TARGET)

