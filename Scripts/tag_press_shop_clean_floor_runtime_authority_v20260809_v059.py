"""Tag the exact clean structural slab so support-robot horizontal sweeps ignore floor contact only."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();SOURCE="/Game/LineBoss/Maps/LB_PressShop_CleanInboundSupportFleetRuntime_v20260809_v056";MAP="/Game/LineBoss/Maps/LB_PressShop_CleanInboundSupportFleetRuntimeFloorFix_v20260809_v059";OUT=ROOT/"Saved/Audits/PressShopIntegration/clean_floor_runtime_authority_v20260809_v059.json";PROTECTED=ROOT/"Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap";EXPECTED="5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper();before=sha(PROTECTED);lib=unreal.EditorAssetLibrary;levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if before!=EXPECTED or lib.does_asset_exist(MAP) or OUT.exists():raise RuntimeError("fresh/protected invariant")
if not levels.new_level_from_template(MAP,SOURCE):raise RuntimeError("map child failed")
floor=[a for a in actors.get_all_level_actors() if a.get_actor_label()=="LB_CLEAN_Floor_220m_x_120m"]
if len(floor)!=1:raise RuntimeError("expected one structural slab")
floor[0].tags=list(floor[0].tags)+[unreal.Name("LB.Environment.Floor.SealedConcrete"),unreal.Name("LB.CleanRebuild.StructuralSlab.RuntimeAuthority")]
if not levels.save_current_level():raise RuntimeError("save failed")
after=sha(PROTECTED)
if after!=before:raise RuntimeError("protected changed")
mf=ROOT/"Content/LineBoss/Maps/LB_PressShop_CleanInboundSupportFleetRuntimeFloorFix_v20260809_v059.umap";OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({"status":"PASS_BUILD__EXACT_STRUCTURAL_SLAB_TAGGED_FOR_RUNTIME_FLOOR_CONTACT__PIE_REPEAT_REQUIRED__NOT_PROMOTED","generated_utc":datetime.now(timezone.utc).isoformat(),"source":SOURCE,"map":MAP,"map_sha256":sha(mf),"floor_actor":floor[0].get_actor_label(),"tags":[str(x) for x in floor[0].tags],"meshy_credits_used":0,"protected_v438_before":before,"protected_v438_after":after},indent=2),encoding="utf-8")
