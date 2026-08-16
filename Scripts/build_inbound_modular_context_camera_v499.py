"""Camera-only successor of failed/occluded inbound context review v498."""
import unreal
SRC="/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryContextReview_v498"
DST="/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryContextReview_v499"
library=unreal.EditorAssetLibrary;levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(DST): raise RuntimeError(f"Refusing overwrite {DST}")
if not library.duplicate_asset(SRC,DST): raise RuntimeError("Could not duplicate v498 to v499")
if not levels.load_level(DST): raise RuntimeError("Could not load v499")
cam=next((a for a in actors.get_all_level_actors() if a.get_actor_label()=="LB_CAM_InboundCoilDelivery_Context_v498"),None)
if cam is None: raise RuntimeError("Missing inherited v498 camera")
cam.set_actor_label("LB_CAM_InboundCoilDelivery_Context_v499")
cam.set_actor_location(unreal.Vector(380,-1550,950),False,False)
cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(cam.get_actor_location(),unreal.Vector(0,260,190)),False)
cam.camera_component.set_editor_properties({"field_of_view":62.0,"aspect_ratio":16/9,"constrain_aspect_ratio":True})
if not levels.save_current_level(): raise RuntimeError("Failed saving v499")
unreal.log("LINE_BOSS_INBOUND_CONTEXT_CAMERA_V499_BUILD_PASS")
