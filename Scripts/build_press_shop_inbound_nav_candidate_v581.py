"""Add bounded pedestrian/service navigation coverage to the west receiving bay."""
from datetime import datetime, timezone
from pathlib import Path
import json, unreal

MAP = "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundNavCandidate_v581"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/inbound_nav_build_v581.json"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP): raise RuntimeError(MAP)
label="LB_INBOUND_V581_NavBounds_WestReceivingBay"
if any(a.get_actor_label()==label for a in actors.get_all_level_actors()): raise RuntimeError("Refusing duplicate nav bounds")
bounds=actors.spawn_actor_from_class(unreal.NavMeshBoundsVolume, unreal.Vector(-11450,-2400,350), unreal.Rotator())
if not bounds: raise RuntimeError("Could not spawn inbound nav bounds")
bounds.set_actor_label(label)
bounds.set_actor_scale3d(unreal.Vector(42.5,24.0,3.5))
bounds.tags=[unreal.Name(v) for v in ("LB.Asset.Candidate.v581","LB.Asset.CandidateNotPromoted",
    "LB.Inbound.Navigation","LB.Navigation.LocalCoverage","LB.Navigation.WestReceivingBay.v581")]
for actor in actors.get_all_level_actors():
    if isinstance(actor,unreal.RecastNavMesh):
        actor.set_editor_property("runtime_generation",unreal.RuntimeGenerationType.DYNAMIC)
        actor.set_editor_property("can_be_main_nav_data",True)
if not levels.save_current_level(): raise RuntimeError("Could not save v581")
origin,extent=bounds.get_actor_bounds(False,False)
payload={"$schema":"cairnwell/audit/press-shop-inbound-nav-build-v581/v1",
 "generated_utc":datetime.now(timezone.utc).isoformat(),"status":"PASS__BOUNDED_WEST_RECEIVING_NAV_COVERAGE_AUTHORED__PIE_REQUIRED__NOT_PROMOTED",
 "map":MAP,"bounds":{"label":label,"origin_cm":[origin.x,origin.y,origin.z],"size_cm":[extent.x*2,extent.y*2,extent.z*2]},
 "promotion_authorized":False}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
unreal.log("LINE_BOSS_INBOUND_NAV_BUILD_V581_PASS")
