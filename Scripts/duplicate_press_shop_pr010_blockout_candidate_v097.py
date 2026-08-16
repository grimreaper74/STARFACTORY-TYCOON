"""Create the isolated PR-010 v097 candidate from accepted PR-009 v096."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressShop_PR009Accepted_v096"
TARGET = "/Game/LineBoss/Maps/LB_PressShop_PR010BlockoutCandidate_v097"
OUT = ROOT / "Saved/Audits/PR010_Blockout/duplication_receipt_v097.json"
OUT.parent.mkdir(parents=True, exist_ok=True)
if unreal.EditorAssetLibrary.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite existing candidate: {TARGET}")
if not unreal.EditorAssetLibrary.duplicate_asset(SOURCE, TARGET):
    raise RuntimeError(f"Could not duplicate {SOURCE}")
if not unreal.EditorAssetLibrary.save_asset(TARGET, only_if_is_dirty=False):
    raise RuntimeError(f"Could not save {TARGET}")
receipt = {
    "$schema": "cairnwell/audit/pr010-blockout-duplication-v097/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "source_map": SOURCE,
    "target_map": TARGET,
    "status": "PASS__PR010_V097_ISOLATED_FROM_ACCEPTED_PR009_V096__POPULATION_REQUIRED__NOT_PROMOTED",
    "promotion_authorized": False,
}
OUT.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
