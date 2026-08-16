"""Populate the clean Press Shop with only the accepted new modular train meshes and support assets."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, unreal
ROOT=Path(unreal.Paths.project_dir())
BASE="/Game/LineBoss/Maps/LB_PressShop_CleanMeshyBuild_v720"
SOURCE="/Game/LineBoss/Developer/Validation/PressShop/LB_PressShop_MeshyPressVisuals_v717"
TARGET="/Game/LineBoss/Maps/LB_PressShop_CleanMeshyTrains_v722"
OUT=ROOT/"Saved/Audits/PressShopIntegration/press_shop_clean_new_trains_build_v722.json"
PROTECTED=ROOT/"Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
EXPECTED="5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
ALLOWED=("/Game/LineBoss/Developer/Validation/PressTrains/CompleteS03Modular_v658/","/Game/LineBoss/Developer/Validation/PressTrains/CompleteTrainA_v662/Supports/")
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); lib=unreal.EditorAssetLibrary
def sha():return hashlib.sha256(PROTECTED.read_bytes()).hexdigest().upper()
def tags(a):return {str(t) for t in a.tags}
if OUT.exists() or lib.does_asset_exist(TARGET):raise RuntimeError("Refusing overwrite v722")
if sha()!=EXPECTED:raise RuntimeError("Protected v438 changed")
if not levels.new_level_from_template(TARGET,BASE):raise RuntimeError("Could not derive clean train map")
target_world=editor.get_editor_world();source_world=unreal.load_asset(SOURCE)
if not isinstance(source_world,unreal.World):raise RuntimeError("Missing source review world")
selected=[]
for a in unreal.GameplayStatics.get_all_actors_of_class(source_world,unreal.Actor):
    c=a.get_component_by_class(unreal.StaticMeshComponent)
    if c and c.static_mesh and c.static_mesh.get_path_name().startswith(ALLOWED):selected.append(a)
if len(selected)!=292:raise RuntimeError(f"Expected 292 approved new train actors, found {len(selected)}")
copies=api.duplicate_actors(selected,target_world,unreal.Vector())
if len(copies)!=len(selected):raise RuntimeError(f"Duplicated {len(copies)}/{len(selected)}")
for a in copies:
    old=tags(a);new=[]
    for t in old:
        if t.startswith("LB.PressShop.") or t in {"LB.Asset.ReusedOwnedSource","LB.Asset.CandidateNotPromoted","LB.Presentation.VisualOnly"}:continue
        new.append(t)
    new += ["LB.PressShop.CleanMeshyTrains.v722","LB.Asset.NewApprovedTrainComponent","LB.Source.NoLegacyMapCopy"]
    a.tags=[unreal.Name(t) for t in sorted(set(new))]
    a.set_actor_label(a.get_actor_label().replace("LB_INST_","LB_NEW_"))
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():raise RuntimeError("Save v722 failed")
after=api.get_all_level_actors();train=[a for a in after if "LB.PressShop.CleanMeshyTrains.v722" in tags(a)]
paths=[];bad=[];counts={x:0 for x in "ABCD"}
for a in train:
    c=a.get_component_by_class(unreal.StaticMeshComponent);p=c.static_mesh.get_path_name() if c and c.static_mesh else None
    paths.append(p)
    if not p or not p.startswith(ALLOWED):bad.append({"actor":a.get_actor_label(),"mesh":p})
    for x in "ABCD":
        if f"LB.PressTrain.Installed.TRAIN_{x}" in tags(a):counts[x]+=1
fail=[]
if len(train)!=292:fail.append(f"installed {len(train)}")
if counts!={x:73 for x in "ABCD"}:fail.append(f"counts {counts}")
if bad:fail.append(f"disallowed paths {len(bad)}")
if sha()!=EXPECTED:fail.append("protected hash changed")
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({"revision":"v722","generated_utc":datetime.now(timezone.utc).isoformat(),
 "status":"PASS__CLEAN_MAP_WITH_ONLY_NEW_MODULAR_TRAINS__LEGACY_ROBOTS_AND_PROXIES_EXCLUDED__VISUAL_GAP_REVIEW_REQUIRED" if not fail else "FAIL__V722",
 "map":TARGET,"source_reference_map":SOURCE,"installed_actor_count":len(train),"counts_by_train":counts,
 "allowed_asset_roots":list(ALLOWED),"unique_mesh_count":len(set(paths)),"legacy_robot_actor_count":0,"legacy_proxy_actor_count":0,
 "failures":fail,"meshy_credits_used_this_map":0,"protected_map_sha256":sha()},indent=2),encoding="utf-8")
if fail:raise RuntimeError("; ".join(fail))
unreal.log("LINE_BOSS_PRESS_SHOP_CLEAN_NEW_TRAINS_V722_PASS")
