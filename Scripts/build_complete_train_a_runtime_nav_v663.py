"""Derive v662 into a fresh runtime/navigation validation map."""
from pathlib import Path
import json,unreal
ROOT=Path(unreal.Paths.project_dir());BASE="/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainA_CompleteModular_v662";MAP="/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainA_RuntimeNav_v663"
OUT=ROOT/r"Saved\Audits\PressTrains\complete_train_a_runtime_nav_build_v663.json"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);library=unreal.EditorAssetLibrary
if library.does_asset_exist(MAP) or OUT.exists():raise RuntimeError("Refusing to overwrite v663")
if not levels.new_level_from_template(MAP,BASE):raise RuntimeError("Could not derive v663")
bootstrap=actors.spawn_actor_from_class(unreal.LBPressShopNavigationBootstrap,unreal.Vector(-900,0,20),unreal.Rotator());bootstrap.set_actor_label("LB_TrainA_NavigationBootstrap_v663");bootstrap.tags=[unreal.Name("LB.Navigation.RuntimeAuthority"),unreal.Name("LB.Asset.CandidateNotPromoted")]
start=actors.spawn_actor_from_class(unreal.PlayerStart,unreal.Vector(-900,0,100),unreal.Rotator());start.set_actor_label("LB_TrainA_PlayerStart_v663");start.tags=[unreal.Name("LB.Validation.PlayerStart"),unreal.Name("LB.Asset.CandidateNotPromoted")]
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():raise RuntimeError("Failed saving v663")
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({"revision":"v663","status":"PASS__RUNTIME_NAV_DERIVATION__PIE_PENDING","map":MAP,"source":BASE,"navigation_bootstraps":1,"player_starts":1,"protected_map_modified":False,"promotion_authorized":False},indent=2),encoding="utf-8")
unreal.log("LINE_BOSS_COMPLETE_TRAIN_A_V663_BUILD_PASS")
