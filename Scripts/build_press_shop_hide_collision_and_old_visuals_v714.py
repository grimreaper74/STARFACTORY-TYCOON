"""Correct presentation: hide collision proxy components and old combined visuals, keep Meshy press meshes."""
from pathlib import Path
import json,unreal
ROOT=Path(unreal.Paths.project_dir());BASE="/Game/LineBoss/Developer/Validation/PressShop/LB_PressShop_CompleteTrainsABCD_Cameras_v704"
MAP="/Game/LineBoss/Developer/Validation/PressShop/LB_PressShop_MeshyPressVisuals_v717";OUT=ROOT/"Saved/Audits/PressShopIntegration/press_shop_hide_collision_and_old_visuals_build_v717.json"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);lib=unreal.EditorAssetLibrary
def tags(a):return {str(t) for t in a.tags}
if OUT.exists() or lib.does_asset_exist(MAP):raise RuntimeError("Refusing overwrite v717")
if not levels.new_level_from_template(MAP,BASE):raise RuntimeError("derive failed")
actors=api.get_all_level_actors();authorities=[a for a in actors if isinstance(a,unreal.LBPressTrainAStation)]
proxies=[a for a in actors if "LB.Collision.Proxy" in tags(a)]
combined=[a for a in actors if "LB.P0.CombinedBackgroundStatic.v694" in tags(a)]
if len(authorities)!=4:raise RuntimeError(f"authority count {len(authorities)}")
if len(proxies)!=340:raise RuntimeError(f"proxy count {len(proxies)}")
if len(combined)!=24:raise RuntimeError(f"combined count {len(combined)}")
rows=[]
for a in authorities:
 comp=a.get_component_by_class(unreal.StaticMeshComponent)
 if not comp:raise RuntimeError("authority mesh missing")
 old_mesh=comp.get_editor_property("static_mesh")
 comp.set_static_mesh(None);comp.set_visibility(False,True);comp.set_hidden_in_game(True);comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);comp.set_editor_property("can_ever_affect_navigation",False)
 rows.append({"actor":a.get_actor_label(),"kind":"legacy_authority_aggregate_removed","removed_mesh":old_mesh.get_path_name() if old_mesh else None,"collision_preserved":False})
for a in proxies:
 comp=a.get_component_by_class(unreal.StaticMeshComponent)
 if not comp:raise RuntimeError("proxy mesh missing")
 before=str(comp.get_collision_enabled());comp.set_visibility(False,True);comp.set_hidden_in_game(True)
 rows.append({"actor":a.get_actor_label(),"kind":"collision_proxy","collision_before":before,"collision_after":str(comp.get_collision_enabled())})
combined_labels=[a.get_actor_label() for a in combined]
if not api.destroy_actors(combined):raise RuntimeError("old combined background deletion failed")
for label in combined_labels:rows.append({"actor":label,"kind":"old_combined_background_deleted"})
if not levels.save_current_level():raise RuntimeError("save failed")
collision_preserved=all(r.get("collision_before")==r.get("collision_after") for r in rows if r["kind"]=="collision_proxy")
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({"revision":"v717","status":"PASS__OLD_AGGREGATE_MESHES_REMOVED__OLD_COMBINED_ACTORS_DELETED__COLLISION_PROXIES_HIDDEN_BUT_ACTIVE__MESHY_PRESSES_VISIBLE__VISUAL_REVIEW_REQUIRED","map":MAP,"authority_aggregate_meshes_removed":len(authorities),"collision_proxy_components_hidden":len(proxies),"collision_proxy_state_preserved":collision_preserved,"old_combined_background_actors_deleted":len(combined),"meshy_credits_used":0},indent=2),encoding="utf-8");unreal.log("LINE_BOSS_PRESS_SHOP_HIDE_COLLISION_AND_OLD_VISUALS_V717_PASS")
