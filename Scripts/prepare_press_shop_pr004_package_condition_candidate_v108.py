"""Prepare the isolated PR-004 package-condition map in its own UE process.

World assets are deliberately duplicated without loading the duplicate. Unreal
must exit before the build process opens it, avoiding retained-world GC faults.
"""

from datetime import datetime, timezone
from pathlib import Path
import json

import unreal


BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004PR005HandoffCandidate_v042"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004PackageConditionCandidate_v108"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_package_condition_prepare_v108.json"

lib = unreal.EditorAssetLibrary

if not lib.does_asset_exist(BASE):
    raise RuntimeError(f"Authoritative v042 base map is missing: {BASE}")

created = False
if not lib.does_asset_exist(MAP):
    if not lib.duplicate_asset(BASE, MAP):
        raise RuntimeError(f"Could not duplicate {BASE} to {MAP}")
    created = True

if not lib.does_asset_exist(MAP):
    raise RuntimeError(f"Prepared map is not registered: {MAP}")

lib.save_asset(MAP, only_if_is_dirty=False)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "$schema": "cairnwell/audit/press-shop-pr004-package-condition-prepare-v108/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "ISOLATED_MAP_PREPARED__NOT_LOADED__NOT_PROMOTED",
    "base_map": BASE,
    "map": MAP,
    "created": created,
    "authority_changed": False,
    "production_map_changed": False,
    "promotion_authorized": False,
}, indent=2), encoding="utf-8")
unreal.log(f"CAIRNWELL_PR004_PACKAGE_CONDITION_V108_PREPARE_PASS created={created}")
unreal.SystemLibrary.quit_editor()
