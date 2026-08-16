"""Duplicate the retained v095 candidate to an isolated v096 correction map."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressShop_PR009EnclosureReleaseCandidate_v095"
DEST = "/Game/LineBoss/Maps/LB_PressShop_PR009FlowAxisCorrectionCandidate_v096"
OUT = ROOT / "Saved/Audits/PR009_InMap_v096/duplication_receipt.json"
OUT.parent.mkdir(parents=True, exist_ok=True)
if unreal.EditorAssetLibrary.does_asset_exist(DEST):
    raise RuntimeError(f"Refusing to overwrite existing v096 map: {DEST}")
asset = unreal.EditorAssetLibrary.duplicate_asset(SOURCE, DEST)
if not asset:
    raise RuntimeError(f"Could not duplicate {SOURCE}")
if not unreal.EditorAssetLibrary.save_asset(DEST, only_if_is_dirty=False):
    raise RuntimeError(f"Could not save {DEST}")
receipt = {
    "$schema": "cairnwell/audit/pr009-flow-axis-v096-duplication/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "source_map": SOURCE,
    "target_map": DEST,
    "status": "PASS__V096_ISOLATED_DUPLICATION__CORRECTION_REQUIRED__NOT_PROMOTED",
    "promotion_authorized": False,
}
OUT.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR009_V096_DUPLICATE {receipt['status']} {OUT}")

