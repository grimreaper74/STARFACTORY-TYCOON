"""Create isolated PR-010 v099 from retained v098."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressShop_PR010DetailedRuntimeCandidate_v098"
TARGET = "/Game/LineBoss/Maps/LB_PressShop_PR010CollisionNavigationCandidate_v099"
OUT = ROOT / "Saved/Audits/PR010_CollisionNavigation/duplication_receipt_v099.json"
OUT.parent.mkdir(parents=True, exist_ok=True)
if unreal.EditorAssetLibrary.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite existing candidate: {TARGET}")
if not unreal.EditorAssetLibrary.duplicate_asset(SOURCE, TARGET):
    raise RuntimeError(f"Could not duplicate {SOURCE}")
if not unreal.EditorAssetLibrary.save_asset(TARGET, only_if_is_dirty=False):
    raise RuntimeError(f"Could not save {TARGET}")
OUT.write_text(json.dumps({
    "$schema": "cairnwell/audit/pr010-collision-navigation-duplication-v099/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "source_map": SOURCE,
    "target_map": TARGET,
    "status": "PASS__PR010_V099_ISOLATED_FROM_RETAINED_V098__COLLISION_NAVIGATION_GATES_REQUIRED__NOT_PROMOTED",
    "promotion_authorized": False,
}, indent=2), encoding="utf-8")
