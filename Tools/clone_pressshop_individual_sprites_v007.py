"""Create an isolated individual-sprite Press Shop candidate from v006."""
import hashlib
import json
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = "/Game/LineBoss/Candidates/PressShop/PressShopFactorio2p5D_Full_v006_TopdownSprite/Maps/LB_PressShop_Factorio2p5D_Full_v006_TopdownSprite"
TARGET = "/Game/LineBoss/Candidates/PressShop/PressShopFactorio2p5D_IndividualSprites_v007/Maps/LB_PressShop_Factorio2p5D_IndividualSprites_v007"
SOURCE_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShopFactorio2p5D_Full_v006_TopdownSprite" / "Maps" / "LB_PressShop_Factorio2p5D_Full_v006_TopdownSprite.umap"
TARGET_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShopFactorio2p5D_IndividualSprites_v007" / "Maps" / "LB_PressShop_Factorio2p5D_IndividualSprites_v007.umap"
PROTECTED_MAPS = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_individual_sprites_v007_clone.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


def fail(message):
    raise RuntimeError("PRESSSHOP_INDIVIDUAL_SPRITES_V007_CLONE_FAIL: " + message)


if not SOURCE_FILE.is_file():
    fail("v006 source map missing")
for path, expected in PROTECTED_MAPS.items():
    if not path.is_file() or digest(path) != expected:
        fail("protected map missing or changed: {}".format(path))
if TARGET_FILE.exists() or unreal.EditorAssetLibrary.does_asset_exist(TARGET):
    fail("refusing to overwrite existing v007 candidate")

before = {"v006_source": digest(SOURCE_FILE)}
before.update({str(path): digest(path) for path in PROTECTED_MAPS})
if not unreal.EditorAssetLibrary.duplicate_asset(SOURCE, TARGET):
    fail("Unreal failed to duplicate v006 into v007")
target = unreal.load_asset(TARGET)
if target is None or not unreal.EditorAssetLibrary.save_loaded_asset(target, only_if_is_dirty=False):
    fail("could not save v007 candidate")
after = {"v006_source": digest(SOURCE_FILE)}
after.update({str(path): digest(path) for path in PROTECTED_MAPS})
if before != after:
    fail("v006 source or protected evidence changed while cloning")

record = {
    "status": "PASS__V007_INDIVIDUAL_SPRITES_CANDIDATE_CLONED",
    "source": SOURCE,
    "target": TARGET,
    "source_sha256": before["v006_source"],
    "target_sha256": digest(TARGET_FILE),
    "evidence_unchanged_before_after": True,
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_INDIVIDUAL_SPRITES_V007_CLONE_PASS=" + json.dumps(record, sort_keys=True))
