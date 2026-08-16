"""Disable retained legacy aggregate meshes on four authorities; keep native gameplay actors active."""
from pathlib import Path
import json,unreal
ROOT=Path(unreal.Paths.project_dir());BASE="/Game/LineBoss/Developer/Validation/PressShop/LB_PressShop_OpenFramePresses_v707"
MAP="/Game/LineBoss/Developer/Validation/PressShop/LB_PressShop_NewPressVisualsOnly_v709";OUT=ROOT/"Saved/Audits/PressShopIntegration/press_shop_remove_legacy_aggregate_build_v709.json"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);lib=unreal.EditorAssetLibrary
if OUT.exists() or lib.does_asset_exist(MAP):raise RuntimeError("Refusing overwrite v709")
if not levels.new_level_from_template(MAP,BASE):raise RuntimeError("derive failed")
auth=[a for a in api.get_all_level_actors() if isinstance(a,unreal.LBPressTrainAStation)]
if len(auth)!=4:raise RuntimeError(f"authority count {len(auth)}")
rows=[]
for a in auth:
 comp=a.get_component_by_class(unreal.StaticMeshComponent)
 mesh=comp.get_editor_property("static_mesh") if comp else None
 if not comp or not mesh:raise RuntimeError("authority aggregate missing on "+a.get_actor_label())
 comp.set_visibility(False,True);comp.set_hidden_in_game(True);comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);comp.set_editor_property("can_ever_affect_navigation",False)
 a.tags=list(a.tags)+[unreal.Name("LB.VisualCorrection.LegacyAggregateDisabled.v709")]
 rows.append({"authority":a.get_actor_label(),"disabled_aggregate":mesh.get_path_name()})
if not levels.save_current_level():raise RuntimeError("save failed")
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({"revision":"v709","status":"PASS__LEGACY_AGGREGATES_DISABLED__NATIVE_AUTHORITIES_RETAINED__VISUAL_REVIEW_REQUIRED","map":MAP,"authorities":rows,"authority_count":4,"gameplay_authorities_removed":0,"meshy_credits_used":0},indent=2),encoding="utf-8");unreal.log("LINE_BOSS_PRESS_SHOP_REMOVE_LEGACY_AGGREGATE_V709_PASS")
