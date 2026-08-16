"""Close the authored 10.5 m nav-coverage gap to retained PR-004 coverage."""
import unreal
MAP="/Game/LineBoss/Developer/Validation/LB_PressShop_InboundNavConnectedCandidate_v586"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):raise RuntimeError(MAP)
rows=[a for a in actors.get_all_level_actors() if a.get_actor_label()=="LB_INBOUND_V581_NavBounds_WestReceivingBay"]
if len(rows)!=1:raise RuntimeError(f"Expected one v581 nav bounds, found {len(rows)}")
bounds=rows[0];bounds.set_actor_location(unreal.Vector(-10500,-2400,350),False,False);bounds.set_actor_scale3d(unreal.Vector(55,24,3.5))
bounds.set_actor_label("LB_INBOUND_V586_NavBounds_WestBayToPR004")
bounds.tags=[unreal.Name(v) for v in ("LB.Asset.Candidate.v586","LB.Asset.CandidateNotPromoted","LB.Inbound.Navigation","LB.Navigation.LocalCoverage","LB.Navigation.WestBayToPR004.v586")]
if not levels.save_current_level():raise RuntimeError("Could not save v586")
unreal.log("LINE_BOSS_INBOUND_NAV_CONNECTED_BUILD_V586_PASS")
