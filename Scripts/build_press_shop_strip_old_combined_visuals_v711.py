"""Strip block-like press shells and retained combined P0 backgrounds; retain separated new machinery."""
from pathlib import Path
import json,unreal
ROOT=Path(unreal.Paths.project_dir());BASE="/Game/LineBoss/Developer/Validation/PressShop/LB_PressShop_NewPressVisualsOnly_v709"
MAP="/Game/LineBoss/Developer/Validation/PressShop/LB_PressShop_StrippedNewPresses_v711";OUT=ROOT/"Saved/Audits/PressShopIntegration/press_shop_strip_old_combined_visuals_build_v711.json"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);lib=unreal.EditorAssetLibrary
def tags(a):return {str(t) for t in a.tags}
if OUT.exists() or lib.does_asset_exist(MAP):raise RuntimeError("Refusing overwrite v711")
if not levels.new_level_from_template(MAP,BASE):raise RuntimeError("derive failed")
actors=api.get_all_level_actors();shells=[a for a in actors if "_StaticPressShell_" in a.get_actor_label() and any(f"LB.PressTrain.Installed.TRAIN_{x}" in tags(a) for x in "ABCD")]
combined=[a for a in actors if "LB.P0.CombinedBackgroundStatic.v694" in tags(a)]
if len(shells)!=20:raise RuntimeError(f"shell count {len(shells)}")
if len(combined)!=24:raise RuntimeError(f"combined background count {len(combined)}")
for a in shells+combined:a.set_actor_hidden_in_game(True);a.set_is_temporarily_hidden_in_editor(True);a.tags=list(a.tags)+[unreal.Name("LB.VisualCorrection.ObsoleteCombinedVisualHidden.v711")]
if not levels.save_current_level():raise RuntimeError("save failed")
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({"revision":"v711","status":"PASS__BLOCK_SHELLS_AND_OLD_COMBINED_BACKGROUNDS_HIDDEN__VISUAL_REVIEW_REQUIRED","map":MAP,"hidden_static_press_shells":len(shells),"hidden_old_combined_backgrounds":len(combined),"separated_p0_actor_count":sum("LB.P0.SeparatedPresentation.v694" in tags(a) for a in actors),"gameplay_authorities_removed":0,"meshy_credits_used":0},indent=2),encoding="utf-8");unreal.log("LINE_BOSS_PRESS_SHOP_STRIP_OLD_COMBINED_VISUALS_V711_PASS")
