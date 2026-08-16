"""Clone the populated v006 world using Save As so external actors follow."""
import json
from pathlib import Path
import unreal
BASE="/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006"
DEST="/Game/LineBoss/Maps/LB_PressShop_PR003StorageCandidate_v014"
OUT=Path(unreal.Paths.project_saved_dir())/"Audits/press_shop_pr003_storage_clone_v014.json"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if unreal.EditorAssetLibrary.does_asset_exist(DEST): raise RuntimeError(f"Refusing to overwrite {DEST}")
if not levels.new_level_from_template(DEST,BASE): raise RuntimeError(f"Template clone failed for {DEST}")
before=None
after=len(actors.get_all_level_actors())
if after < 100: raise RuntimeError(f"Cloned population unexpectedly low: {after}")
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({"status":"CLONED_NOT_PROMOTED","base_map":BASE,"map":DEST,"actors_before":before,"actors_after":after},indent=2),encoding="utf-8")
unreal.log(f"LINE_BOSS_PR003_STORAGE_V014_CLONE_PASS actors={after}")
unreal.SystemLibrary.quit_editor()
