"""Create a fresh installed-context successor of inbound review v489."""
import unreal
BASE="/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryReview_v489"
MAP="/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryReview_v492"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem); library=unreal.EditorAssetLibrary
if library.does_asset_exist(MAP): raise RuntimeError(f"Refusing overwrite: {MAP}")
if not levels.new_level_from_template(MAP,BASE): raise RuntimeError("Could not derive v492 from v489")
cube=library.load_asset("/Engine/BasicShapes/Cube.Cube")
charcoal=library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_Charcoal_v001")
yellow=library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_SafetyYellow_v001")
def primitive(label,loc,scale,mat):
    a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc),unreal.Rotator()); a.set_actor_label(label); a.set_actor_scale3d(unreal.Vector(*scale)); a.static_mesh_component.set_static_mesh(cube); a.static_mesh_component.set_material(0,mat); a.tags=[unreal.Name("LB.Asset.ValidationOnly"),unreal.Name("LB.Asset.CandidateNotPromoted"),unreal.Name("LB.Crane.Support.TBC")]; return a
# Review-only gantry supports at the bridge endpoints; dimensions remain TBC.
primitive("LB_INBOUND_CraneColumn_A_TBC",(0,285,350),(0.28,0.28,7.0),charcoal)
primitive("LB_INBOUND_CraneColumn_B_TBC",(0,855,350),(0.28,0.28,7.0),charcoal)
primitive("LB_INBOUND_HoistReeving_TBC",(0,600,565),(0.045,0.045,2.2),yellow)
for a in actors.get_all_level_actors():
    if a.get_actor_label()=="LB_CAM_InboundCoilDelivery_v489": a.set_actor_label("LB_CAM_InboundCoilDelivery_v492")
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level(): raise RuntimeError("Failed saving v492")
unreal.log("LINE_BOSS_INBOUND_REVIEW_V492_BUILD_PASS")
