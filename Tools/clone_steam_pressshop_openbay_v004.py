"""Clone the v004 candidate only; load it in a fresh Unreal session afterwards.

UE 5.8 can retain a transient UWorld when a map is both duplicated and loaded
by a single Python invocation. This small pass deliberately stops after the
safe duplication. The separate population pass loads the map after restart.
"""
import hashlib
import json
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = "/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryInstalledCell_v551"
TARGET = "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/Maps/LB_PressShop_SteamOpenBay_v004"
SOURCE_FILE = PROJECT / "Content" / "LineBoss" / "Developer" / "Validation" / "LB_InboundCoilDeliveryInstalledCell_v551.umap"
TARGET_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "SquareMeshyPressTrain_v001" / "Maps" / "LB_PressShop_SteamOpenBay_v004.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "steam_openbay_clone_v004.json"


def fail(message):
    raise RuntimeError("STEAM_OPEN_BAY_V004_CLONE_FAIL: " + message)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


if not SOURCE_FILE.is_file():
    fail("retained v551 source map is missing")
if unreal.EditorAssetLibrary.does_asset_exist(TARGET) or TARGET_FILE.exists():
    fail("v004 target already exists; refusing overwrite")
before_hash = sha256(SOURCE_FILE)
before_mtime = SOURCE_FILE.stat().st_mtime_ns
if not unreal.EditorAssetLibrary.duplicate_asset(SOURCE, TARGET):
    fail("Unreal did not duplicate the retained v551 source")
target = unreal.load_asset(TARGET)
if target is None:
    fail("duplicated candidate cannot be resolved")
if not unreal.EditorAssetLibrary.save_loaded_asset(target, only_if_is_dirty=False):
    fail("duplicated candidate could not be saved")
if not TARGET_FILE.is_file():
    fail("candidate map file was not written")
after_hash = sha256(SOURCE_FILE)
after_mtime = SOURCE_FILE.stat().st_mtime_ns
if before_hash != after_hash or before_mtime != after_mtime:
    fail("retained v551 source changed during clone")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__V004_OPEN_BAY_CANDIDATE_CLONED_ONLY__RESTART_REQUIRED_BEFORE_POPULATION",
    "source": SOURCE,
    "target": TARGET,
    "source_sha256_before": before_hash,
    "source_sha256_after": after_hash,
    "source_mtime_ns_before": before_mtime,
    "source_mtime_ns_after": after_mtime,
    "target_sha256": sha256(TARGET_FILE),
    "safety": "candidate clone only; deliberately not loaded in this editor session to avoid UE 5.8 UWorld leak",
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("STEAM_OPEN_BAY_V004_CLONE_PASS=" + TARGET)
