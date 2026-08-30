"""Duplicate the camera-locked v004 candidate before flow-aligning its S02 art."""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = "/Game/LineBoss/Candidates/PressShop/PressShopFactorio2p5D_Full_v004_CameraLockedSprites/Maps/LB_PressShop_Factorio2p5D_Full_v004_CameraLockedSprites"
TARGET = "/Game/LineBoss/Candidates/PressShop/PressShopFactorio2p5D_Full_v005_FlowAlignedSprites/Maps/LB_PressShop_Factorio2p5D_Full_v005_FlowAlignedSprites"
SOURCE_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShopFactorio2p5D_Full_v004_CameraLockedSprites" / "Maps" / "LB_PressShop_Factorio2p5D_Full_v004_CameraLockedSprites.umap"
TARGET_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShopFactorio2p5D_Full_v005_FlowAlignedSprites" / "Maps" / "LB_PressShop_Factorio2p5D_Full_v005_FlowAlignedSprites.umap"
PROTECTED = {
    "v438": PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap",
    "steam_v002": PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap",
}
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_factorio_2p5d_full_v005_flow_aligned_clone.json"

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()

if not SOURCE_FILE.is_file() or any(not path.is_file() for path in PROTECTED.values()):
    raise RuntimeError("source or protected map missing")
if TARGET_FILE.exists() or unreal.EditorAssetLibrary.does_asset_exist(TARGET):
    raise RuntimeError("flow-aligned target already exists")
before = {"source_v004": digest(SOURCE_FILE)}
before.update({name: digest(path) for name, path in PROTECTED.items()})
if not unreal.EditorAssetLibrary.duplicate_asset(SOURCE, TARGET):
    raise RuntimeError("Unreal could not duplicate v004")
target = unreal.load_asset(TARGET)
if target is None or not unreal.EditorAssetLibrary.save_loaded_asset(target, only_if_is_dirty=False):
    raise RuntimeError("could not save v005 candidate")
after = {"source_v004": digest(SOURCE_FILE)}
after.update({name: digest(path) for name, path in PROTECTED.items()})
if before != after:
    raise RuntimeError("source or protected evidence changed during clone")
record = {
    "status": "PASS__V005_FLOW_ALIGNED_SPRITE_CANDIDATE_CLONED",
    "source": SOURCE, "target": TARGET, "source_hash": before["source_v004"],
    "target_hash": digest(TARGET_FILE), "evidence_before": before, "evidence_after": after,
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2P5D_V005_FLOW_ALIGNED_CLONE_PASS=" + json.dumps(record, sort_keys=True))

