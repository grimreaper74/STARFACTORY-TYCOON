"""Native map-asset duplication pass. Deliberately does not reload the new world."""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = "/Game/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001"
DEST = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
SOURCE_FILE = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_FullFactoryRestored_v001.umap"
SOURCE_SHA256 = "d3f8652aa45e7c2fcee5af1971f6aa78a3f027e60e361b039d14dad5806c74a5"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "duplicate_fullhall_v001_receipt.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


if digest(SOURCE_FILE) != SOURCE_SHA256:
    raise RuntimeError("restored source changed")
if unreal.EditorAssetLibrary.does_asset_exist(DEST):
    raise RuntimeError("refusing to overwrite existing destination")
if not unreal.EditorAssetLibrary.duplicate_asset(SOURCE, DEST):
    raise RuntimeError("map duplication failed")
if not unreal.EditorAssetLibrary.save_asset(DEST, only_if_is_dirty=False):
    raise RuntimeError("duplicated map asset did not save")
dest_file = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_FullHall_v001" / "Maps" / "LB_PressShop_2126_FullHall_v001.umap"
if not dest_file.is_file():
    raise RuntimeError("duplicated map file missing after save")
RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__MAP_ASSET_DUPLICATED",
    "source": SOURCE,
    "source_sha256": SOURCE_SHA256,
    "destination": DEST,
    "destination_file": str(dest_file),
    "destination_sha256": digest(dest_file),
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2126_FULLHALL_DUPLICATE_PASS {}".format(RECEIPT))
unreal.SystemLibrary.quit_editor()
