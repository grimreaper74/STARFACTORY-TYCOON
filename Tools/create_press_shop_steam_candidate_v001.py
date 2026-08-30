"""Create a protected-source clone for Press Shop Steam work.

The builder-authority v438 map is evidence and is never opened for editing,
saved, or renamed.  This script only duplicates its package to a new candidate
package, then proves that the protected source bytes did not change.
"""
import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = "/Game/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438"
TARGET = "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/Maps/LB_PressShop_SteamCandidate_v001"
SOURCE_FILE = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
TARGET_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "SquareMeshyPressTrain_v001" / "Maps" / "LB_PressShop_SteamCandidate_v001.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "press_shop_steam_candidate_clone_v001.json"


def fail(message):
    raise RuntimeError("PRESS_SHOP_STEAM_CANDIDATE_CLONE_FAIL: " + message)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


if not SOURCE_FILE.is_file():
    fail("protected v438 source map file is missing")
if unreal.EditorAssetLibrary.does_asset_exist(TARGET) or TARGET_FILE.exists():
    fail("target candidate already exists; refusing to overwrite evidence")

source_hash_before = sha256(SOURCE_FILE)
source_mtime_before_ns = SOURCE_FILE.stat().st_mtime_ns
if not unreal.EditorAssetLibrary.duplicate_asset(SOURCE, TARGET):
    fail("Unreal did not duplicate protected v438 map into the candidate package")
# Asset duplication creates the target package in memory.  Explicitly save the
# new target before testing the filesystem; otherwise a headless commandlet can
# exit with a successful in-memory duplicate and no durable candidate map.
target_asset = unreal.load_asset(TARGET)
if target_asset is None:
    fail("duplicated target package could not be loaded")
if not unreal.EditorAssetLibrary.save_loaded_asset(target_asset, only_if_is_dirty=False):
    fail("could not save the duplicated target package")
if not TARGET_FILE.is_file():
    fail("target candidate file was not written")

source_hash_after = sha256(SOURCE_FILE)
source_mtime_after_ns = SOURCE_FILE.stat().st_mtime_ns
if source_hash_after != source_hash_before or source_mtime_after_ns != source_mtime_before_ns:
    fail("protected v438 source map changed during clone operation")

report = {
    "status": "PASS__PROTECTED_V438_CLONED_TO_NEW_STEAM_CANDIDATE",
    "source": SOURCE,
    "target": TARGET,
    "source_sha256_before": source_hash_before,
    "source_sha256_after": source_hash_after,
    "source_mtime_ns_before": source_mtime_before_ns,
    "source_mtime_ns_after": source_mtime_after_ns,
    "target_sha256": sha256(TARGET_FILE),
    "target_bytes": TARGET_FILE.stat().st_size,
    "scope": "candidate-only clone; v438 remains protected evidence and must not be opened for authoring or saved",
    "next_gate": "inspect clone in full Unreal Editor before placing any candidate assets or changing lighting",
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("LINE_BOSS_PRESS_SHOP_STEAM_CANDIDATE_CLONE=" + json.dumps(report, sort_keys=True))
