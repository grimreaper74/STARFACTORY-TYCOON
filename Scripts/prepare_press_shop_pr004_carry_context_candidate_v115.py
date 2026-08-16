"""Prepare isolated PR-004 carry-context v115 from retained v113."""
from pathlib import Path
from datetime import datetime, timezone
import json
import unreal

BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004SupportIdentityCandidate_v113"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004CarryContextCandidate_v115"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_carry_context_prepare_v115.json"
lib = unreal.EditorAssetLibrary
if not lib.does_asset_exist(BASE):
    raise RuntimeError(f"Missing retained v113 base: {BASE}")
created = False
if not lib.does_asset_exist(MAP):
    if not lib.duplicate_asset(BASE, MAP):
        raise RuntimeError(f"Could not duplicate {BASE} to {MAP}")
    created = True
lib.save_asset(MAP, only_if_is_dirty=False)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "$schema": "cairnwell/audit/press-shop-pr004-carry-context-prepare-v115/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "ISOLATED_MAP_PREPARED__NOT_LOADED__NOT_PROMOTED",
    "base_map": BASE, "map": MAP, "created": created,
    "authority_changed": False, "production_map_changed": False,
    "promotion_authorized": False
}, indent=2), encoding="utf-8")
unreal.log(f"CAIRNWELL_PR004_CARRY_CONTEXT_V115_PREPARE_PASS created={created}")
unreal.SystemLibrary.quit_editor()
