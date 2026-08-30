"""Clone the complete 2.5D layout before any visible sprite art is mounted.

This is deliberately a one-purpose session: UE 5.8 is not asked to duplicate
and load a UWorld in the same invocation. The next script restarts the editor,
loads only this new candidate, and adds its camera-facing sprite layer.
"""
import hashlib
import json
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = "/Game/LineBoss/Candidates/PressShop/PressShopFactorio2p5D_Full_v001/Maps/LB_PressShop_Factorio2p5D_Full_v001"
TARGET = "/Game/LineBoss/Candidates/PressShop/PressShopFactorio2p5D_Full_v002_SpriteArt/Maps/LB_PressShop_Factorio2p5D_Full_v002_SpriteArt"
SOURCE_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShopFactorio2p5D_Full_v001" / "Maps" / "LB_PressShop_Factorio2p5D_Full_v001.umap"
TARGET_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShopFactorio2p5D_Full_v002_SpriteArt" / "Maps" / "LB_PressShop_Factorio2p5D_Full_v002_SpriteArt.umap"
PROTECTED = {
    "v438": PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap",
    "steam_v002": PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap",
}
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_factorio_2p5d_full_v002_sprite_art_clone.json"

def fail(message):
    raise RuntimeError("PRESSSHOP_2P5D_SPRITE_ART_CLONE_FAIL: " + message)

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

if not SOURCE_FILE.is_file():
    fail("full v001 source map is missing")
if unreal.EditorAssetLibrary.does_asset_exist(TARGET) or TARGET_FILE.exists():
    fail("v002 sprite-art target already exists; refusing overwrite")
if any(not path.is_file() for path in PROTECTED.values()):
    fail("a protected historical map is missing")

before = {"source": sha256(SOURCE_FILE)}
before.update({name: sha256(path) for name, path in PROTECTED.items()})
if not unreal.EditorAssetLibrary.duplicate_asset(SOURCE, TARGET):
    fail("Unreal did not duplicate the full v001 map")
target = unreal.load_asset(TARGET)
if target is None or not unreal.EditorAssetLibrary.save_loaded_asset(target, only_if_is_dirty=False):
    fail("duplicated sprite-art map could not be saved")
if not TARGET_FILE.is_file():
    fail("candidate map file was not written")
after = {"source": sha256(SOURCE_FILE)}
after.update({name: sha256(path) for name, path in PROTECTED.items()})
if before != after:
    fail("source or protected historical evidence changed during the clone")

report = {
    "status": "PASS__FULL_2P5D_LAYOUT_CLONED_FOR_SPRITE_ART__RESTART_REQUIRED_BEFORE_POPULATION",
    "source": SOURCE,
    "target": TARGET,
    "source_sha256_before": before["source"],
    "source_sha256_after": after["source"],
    "target_sha256": sha256(TARGET_FILE),
    "protected_sha256_before": {name: value for name, value in before.items() if name != "source"},
    "protected_sha256_after": {name: value for name, value in after.items() if name != "source"},
    "safety": "candidate clone only; not loaded in this editor session to avoid a UE 5.8 transient UWorld leak",
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2P5D_SPRITE_ART_CLONE_PASS=" + TARGET)
