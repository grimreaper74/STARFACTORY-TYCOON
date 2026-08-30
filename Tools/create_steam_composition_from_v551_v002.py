"""Create a clean Steam-composition candidate from the retained v551 inbound cell.

v551 is the strongest existing lorry-unload visual: lorry, four wrapped coils,
C-hook crane, saddle and AGV read clearly in its open presentation cell.  This
creates a new map only; it does not modify v551, v438, the current v438-derived
candidate, or any shared asset.  The next pass will add the new press line to
this clean visual foundation.
"""
import hashlib
import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = "/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryInstalledCell_v551"
TARGET = "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/Maps/LB_PressShop_SteamComposition_v002"
SOURCE_FILE = PROJECT / "Content" / "LineBoss" / "Developer" / "Validation" / "LB_InboundCoilDeliveryInstalledCell_v551.umap"
TARGET_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "SquareMeshyPressTrain_v001" / "Maps" / "LB_PressShop_SteamComposition_v002.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "steam_composition_from_v551_v002.json"


def fail(message):
    raise RuntimeError("STEAM_COMPOSITION_V551_CLONE_FAIL: " + message)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


if not SOURCE_FILE.is_file():
    fail("v551 source map is missing")
if unreal.EditorAssetLibrary.does_asset_exist(TARGET) or TARGET_FILE.exists():
    fail("v002 target already exists; refusing overwrite")

source_hash_before = sha256(SOURCE_FILE)
source_mtime_before_ns = SOURCE_FILE.stat().st_mtime_ns
if not unreal.EditorAssetLibrary.duplicate_asset(SOURCE, TARGET):
    fail("Unreal did not duplicate v551 to the Steam composition candidate")
target_asset = unreal.load_asset(TARGET)
if target_asset is None:
    fail("duplicated map cannot be loaded")
if not unreal.EditorAssetLibrary.save_loaded_asset(target_asset, only_if_is_dirty=False):
    fail("could not save duplicated candidate")
if not TARGET_FILE.is_file():
    fail("candidate map file was not written")

source_hash_after = sha256(SOURCE_FILE)
source_mtime_after_ns = SOURCE_FILE.stat().st_mtime_ns
if source_hash_before != source_hash_after or source_mtime_before_ns != source_mtime_after_ns:
    fail("retained v551 source map changed during clone")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__RETAINED_V551_CLONED_TO_STEAM_COMPOSITION_V002",
    "source": SOURCE,
    "target": TARGET,
    "source_sha256_before": source_hash_before,
    "source_sha256_after": source_hash_after,
    "source_mtime_ns_before": source_mtime_before_ns,
    "source_mtime_ns_after": source_mtime_after_ns,
    "target_sha256": sha256(TARGET_FILE),
    "target_bytes": TARGET_FILE.stat().st_size,
    "purpose": "clean, readable lorry-unload composition to be extended with the new press train",
    "honest_status": "candidate presentation only; no release, gameplay, collision, navigation, save or build authority",
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("STEAM_COMPOSITION_V551_CLONE=" + json.dumps({"target": TARGET}, sort_keys=True))
