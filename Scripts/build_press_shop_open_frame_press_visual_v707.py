"""Visual experiment: remove block-like modular housings while retaining detailed press frames/tooling."""
from pathlib import Path
import json,unreal
ROOT=Path(unreal.Paths.project_dir());BASE="/Game/LineBoss/Developer/Validation/PressShop/LB_PressShop_CompleteTrainsABCD_Cameras_v704"
MAP="/Game/LineBoss/Developer/Validation/PressShop/LB_PressShop_OpenFramePresses_v707";OUT=ROOT/"Saved/Audits/PressShopIntegration/press_shop_open_frame_press_visual_build_v707.json"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);lib=unreal.EditorAssetLibrary
if OUT.exists() or lib.does_asset_exist(MAP):raise RuntimeError("Refusing overwrite v707")
if not levels.new_level_from_template(MAP,BASE):raise RuntimeError("derive failed")
housings=[a for a in api.get_all_level_actors() if "_Housing_" in a.get_actor_label() and any(f"LB.PressTrain.Installed.TRAIN_{x}" in {str(t) for t in a.tags} for x in "ABCD")]
if len(housings)!=20:raise RuntimeError(f"expected 20 housings, got {len(housings)}")
for a in housings:a.set_actor_hidden_in_game(True);a.set_is_temporarily_hidden_in_editor(True);a.tags=list(a.tags)+[unreal.Name("LB.VisualCorrection.BlockHousingHidden.v707")]
if not levels.save_current_level():raise RuntimeError("save failed")
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({"revision":"v707","status":"PASS__BLOCK_HOUSINGS_HIDDEN__VISUAL_REVIEW_REQUIRED","map":MAP,"hidden_housing_count":len(housings),"gameplay_authority_changed":False,"collision_changed":False,"meshy_credits_used":0},indent=2),encoding="utf-8");unreal.log("LINE_BOSS_PRESS_SHOP_OPEN_FRAME_PRESS_VISUAL_V707_PASS")
