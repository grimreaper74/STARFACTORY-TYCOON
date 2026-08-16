"""Create the immutable accepted PR-009 v095 map from the fully gated candidate."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressShop_PR009EnclosureReleaseCandidate_v095"
DEST = "/Game/LineBoss/Maps/LB_PressShop_PR009Accepted_v095"
VERIFICATION = ROOT / "Saved/Audits/PR009_InMap_v095/PR009_ENCLOSURE_RELEASE_VERIFICATION.json"
OUT = ROOT / "Saved/Audits/PR009_Accepted_v095/duplication_receipt.json"
OUT.parent.mkdir(parents=True, exist_ok=True)

verification = json.loads(VERIFICATION.read_text(encoding="utf-8"))
required = "PASS__PR009_V095_ENCLOSED_CELL_BASELINE_PROMOTION_AUTHORIZED__PRESS_SHOP_NOT_COMPLETE"
if verification.get("status") != required or not verification.get("promotion_authorized"):
    raise RuntimeError("The consolidated v095 gate does not authorize promotion")
if unreal.EditorAssetLibrary.does_asset_exist(DEST):
    raise RuntimeError(f"Accepted map already exists; refusing to overwrite: {DEST}")
duplicated = unreal.EditorAssetLibrary.duplicate_asset(SOURCE, DEST)
if not duplicated:
    raise RuntimeError(f"Could not duplicate {SOURCE} to {DEST}")
if not unreal.EditorAssetLibrary.save_asset(DEST, only_if_is_dirty=False):
    raise RuntimeError(f"Could not save duplicated accepted map: {DEST}")
receipt = {
    "$schema": "cairnwell/audit/pr009-accepted-baseline-duplication-v095/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "source_map": SOURCE,
    "accepted_map": DEST,
    "status": "PASS__PR009_V095_ACCEPTED_BASELINE_DUPLICATED__FINALIZATION_REQUIRED",
    "press_shop_complete": False,
}
OUT.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR009_ACCEPTED {receipt['status']} {OUT}")

