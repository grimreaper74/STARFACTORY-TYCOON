"""Duplicate the accepted v006 map only; edit in a later clean process."""
from pathlib import Path
import json
import unreal
BASE="/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006"
DEST="/Game/LineBoss/Maps/LB_PressShop_PR003StorageCandidate_v012"
OUT=Path(unreal.Paths.project_saved_dir())/"Audits/press_shop_pr003_storage_prepare_v012.json"
if unreal.EditorAssetLibrary.does_asset_exist(DEST): raise RuntimeError(f"Refusing to overwrite {DEST}")
if not unreal.EditorAssetLibrary.duplicate_asset(BASE,DEST): raise RuntimeError(f"Could not duplicate {BASE}")
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({"status":"PREPARED_NOT_PROMOTED","base_map":BASE,"map":DEST,"loaded_destination":False},indent=2),encoding="utf-8")
unreal.log("LINE_BOSS_PR003_STORAGE_V012_PREPARE_PASS")
unreal.SystemLibrary.quit_editor()
