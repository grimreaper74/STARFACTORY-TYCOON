"""Replace retained train scopes in a v438 successor with complete A-D at current widened datums."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import unreal

ROOT=Path(unreal.Paths.project_dir())
BASE="/Game/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438"
TARGET="/Game/LineBoss/Developer/Validation/PressShop/LB_PressShop_CompleteTrainsABCD_v700"
PROTECTED=ROOT/"Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
EXPECTED="5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
OUT=ROOT/"Saved/Audits/PressShopIntegration/press_shop_complete_trains_abcd_build_v700.json"
SOURCES={"A":"/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainA_RuntimeP0_v694",
         **{x:f"/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrain{x}_CompleteVariant_v696" for x in "BCD"}}
DATUMS={"A":(1600.0,-4300.0,0.0),"B":(1600.0,-2100.0,0.0),
        "C":(1600.0,100.0,0.0),"D":(1600.0,2300.0,0.0)}
api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
library=unreal.EditorAssetLibrary
def sha(): return hashlib.sha256(PROTECTED.read_bytes()).hexdigest().upper()
def tags(a): return {str(t) for t in a.tags}
if OUT.exists() or library.does_asset_exist(TARGET): raise RuntimeError("Refusing to overwrite v700")
if sha()!=EXPECTED: raise RuntimeError("Protected v438 hash mismatch before integration")
if not levels.new_level_from_template(TARGET,BASE): raise RuntimeError("Could not derive v700")
target_world=editor.get_editor_world()
existing=api.get_all_level_actors()
old_scope=[a for a in existing if any(f"LB.PressTrain.Installed.TRAIN_{x}" in tags(a) for x in "ABCD")]
old_counts={x:sum(f"LB.PressTrain.Installed.TRAIN_{x}" in tags(a) for a in old_scope) for x in "ABCD"}
if not api.destroy_actors(old_scope): raise RuntimeError("Could not remove retained train scopes in successor")

reports={}
for letter,source_path in SOURCES.items():
    source_world=unreal.load_asset(source_path)
    if not isinstance(source_world,unreal.World): raise RuntimeError(f"Missing source world {source_path}")
    source_all=unreal.GameplayStatics.get_all_actors_of_class(source_world,unreal.Actor)
    scope=f"LB.PressTrain.Installed.TRAIN_{letter}"
    source=[a for a in source_all if scope in tags(a)]
    if len(source)!=182: raise RuntimeError(f"Train {letter}: source scope count {len(source)}")
    snapshots=[(a.get_actor_label(),a.get_actor_location(),a.get_actor_rotation()) for a in source]
    copies=api.duplicate_actors(source,target_world,unreal.Vector())
    if len(copies)!=len(source): raise RuntimeError(f"Train {letter}: duplicated {len(copies)}/{len(source)}")
    tx,ty,tz=DATUMS[letter]
    for actor,(label,loc,rot) in zip(copies,snapshots):
        # Local process +Y becomes shop process +X; authority 0,0,0 lands on the current v438 datum.
        actor.set_actor_location(unreal.Vector(tx+loc.y,ty-loc.x,tz+loc.z),False,False)
        actor.set_actor_rotation(unreal.Rotator(roll=rot.roll,pitch=rot.pitch,yaw=rot.yaw-90.0),False)
        actor.set_actor_label(f"LB_INST_PT{letter}_{label}")
        values=list(tags(actor))
        for value in ("LB.PressShop.CompleteTrainsABCD.v700","LB.Asset.CandidateNotPromoted"):
            if value not in values: values.append(value)
        actor.tags=[unreal.Name(v) for v in sorted(values)]
    authorities=[a for a in copies if isinstance(a,unreal.LBPressTrainAStation)]
    if len(authorities)!=1: raise RuntimeError(f"Train {letter}: authority copies {len(authorities)}")
    reports[letter]={"source_map":source_path,"source_actor_count":len(source),"installed_actor_count":len(copies),
                     "datum_cm":list(DATUMS[letter]),"authority_location_cm":list(authorities[0].get_actor_location().to_tuple()),
                     "authority_yaw_deg":authorities[0].get_actor_rotation().yaw}

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level(): raise RuntimeError("Failed saving v700")
all_after=api.get_all_level_actors()
failures=[]
for letter in "ABCD":
    scope=f"LB.PressTrain.Installed.TRAIN_{letter}"
    members=[a for a in all_after if scope in tags(a)]
    authorities=[a for a in members if isinstance(a,unreal.LBPressTrainAStation)]
    if len(members)!=182: failures.append(f"Train {letter} member count {len(members)}")
    if len(authorities)!=1: failures.append(f"Train {letter} authority count {len(authorities)}")
if sha()!=EXPECTED: failures.append("protected v438 hash changed")
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({"revision":"v700","generated_utc":datetime.now(timezone.utc).isoformat(),
 "status":"PASS__COMPLETE_TRAINS_A_D_AT_CURRENT_WIDENED_V438_DATUMS__STATIC_GATES_PENDING" if not failures else "FAIL__V700",
 "source_shop_map":BASE,"target_map":TARGET,"old_scope_counts_removed_in_successor":old_counts,
 "current_widened_pitch_cm":2200.0,"rotation_yaw_deg":-90.0,"trains":reports,"failures":failures,
 "meshy_credits_used":0,"protected_map_sha256":sha(),"protected_map_modified":False,"promotion_authorized":False},indent=2),encoding="utf-8")
if failures: raise RuntimeError("; ".join(failures))
unreal.log("LINE_BOSS_PRESS_SHOP_COMPLETE_TRAINS_ABCD_V700_PASS")
