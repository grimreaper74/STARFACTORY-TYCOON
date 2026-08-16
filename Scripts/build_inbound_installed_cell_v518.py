"""Fresh v518 camera/exposure successor built from the retained v517 recipe."""
from pathlib import Path
import unreal

root=Path(__file__).parent
source=(root/"build_inbound_installed_cell_v517.py").read_text(encoding="utf-8")
source=source.replace("v517","v518").replace("V517","V518").replace("V017_","V018_")
exec(compile(source,str(root/"build_inbound_installed_cell_v517.py"),"exec"),globals(),globals())

actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
camera=next((a for a in actors.get_all_level_actors() if isinstance(a,unreal.CameraActor)),None)
if camera is None:
    raise RuntimeError("Missing v518 camera")
camera.set_actor_label("LB_CAM_InboundCoilDelivery_OperationalReadability_v518")
camera.set_actor_location(unreal.Vector(0,3150,1500),False,False)
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(),unreal.Vector(260,180,240)),False)
camera.camera_component.set_editor_properties({"field_of_view":55.0,"aspect_ratio":16/9,"constrain_aspect_ratio":True})
for actor in actors.get_all_level_actors():
    if isinstance(actor,unreal.RectLight):
        component=actor.rect_light_component
        component.set_editor_property("intensity",component.get_editor_property("intensity")*.58)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("Failed saving v518 camera/exposure successor")
unreal.log("LINE_BOSS_INBOUND_INSTALLED_CELL_V518_BUILD_PASS")
